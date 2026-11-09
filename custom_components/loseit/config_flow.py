"""Native cookie import with validated session storage."""

import json
import re
from typing import Any

import probatio as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.util import dt as dt_util

from .client import LoseItAuthError, LoseItClient, LoseItError, LoseItRateLimitError
from .const import (
    CONF_COOKIES,
    CONF_POLL_MINUTES,
    CONF_SESSION,
    CONF_SOURCE_TIMEZONE,
    CONF_TIMEZONE,
    DEFAULT_POLL_MINUTES,
    DOMAIN,
)
from .request_gate import session_request_gate


async def async_valid_timezone(value: str) -> str:
    """Validate off the event loop while keeping the form schema serializable."""
    try:
        timezone = await dt_util.async_get_time_zone(value)
    except (ValueError, TypeError) as err:
        raise vol.Invalid("Invalid timezone") from err
    if timezone is None:
        raise vol.Invalid("Invalid timezone")
    return value


def parse_cookies(raw: str) -> dict[str, str]:
    """Import a one-line Cookie value or a legacy JSON cookie dictionary."""
    # Bound both characters and UTF-8 bytes before either parser allocates work.
    if not isinstance(raw, str) or len(raw) > 65536 or len(raw.encode("utf-8")) > 65536:
        raise ValueError("Session input exceeds limit")
    if not raw.lstrip().startswith("{"):
        # Only ASCII cookie-octets; never trim, decode or otherwise alter values.
        if any(ord(char) < 32 or ord(char) > 126 for char in raw):
            raise ValueError("Expected one-line Cookie value")
        header = raw.lstrip(" ")
        if header[:7].lower() == "cookie:":
            header = header[7:].lstrip(" ")
        cookies = {}
        for pair in header.split(";"):
            name, separator, value = pair.lstrip(" ").partition("=")
            if (
                not separator
                or re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name) is None
            ):
                raise ValueError("Invalid Cookie value")
            if name in {"liauth", "fn_auth", "fn_authed"}:
                if (
                    re.fullmatch(r"[\x21\x23-\x2b\x2d-\x3a\x3c-\x5b\x5d-\x7e]*", value)
                    is None
                ):
                    raise ValueError("Invalid Cookie value")
                if name in cookies:
                    raise ValueError("Duplicate session cookie")
                cookies[name] = value
        if not (cookies.get("liauth") or cookies.get("fn_auth")):
            raise ValueError("Missing session cookie")
        return cookies
    value = json.loads(raw)
    if (
        not isinstance(value, dict)
        or not value
        or any(
            not isinstance(k, str) or not k or not isinstance(v, str) or not v
            for k, v in value.items()
        )
    ):
        raise ValueError("Expected a nonempty cookie dictionary")
    return value


class LoseItConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> LoseItOptionsFlow:
        return LoseItOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_session(user_input)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_session(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_session(user_input)

    def _existing_entry(self) -> config_entries.ConfigEntry | None:
        if self.context.get("source") == "reauth":
            return self._get_reauth_entry()
        if self.context.get("source") == "reconfigure":
            return self._get_reconfigure_entry()
        return None

    async def async_step_session(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        existing = self._existing_entry()
        if user_input is not None:
            try:
                timezone = await async_valid_timezone(user_input[CONF_TIMEZONE])
                cookies = parse_cookies(user_input[CONF_SESSION])
            except (KeyError, ValueError, TypeError, RecursionError, vol.Invalid):
                errors["base"] = "invalid_input"
            else:
                try:
                    gate = session_request_gate(self.hass)
                    session = async_get_clientsession(self.hass)
                    account = await gate.async_get_account(
                        self.hass,
                        cookies,
                        LoseItClient(session, cookies),
                        existing,
                    )
                except LoseItAuthError:
                    errors["base"] = "invalid_auth"
                except LoseItRateLimitError:
                    errors["base"] = "rate_limited"
                except (LoseItError, TimeoutError):
                    errors["base"] = "cannot_connect"
                else:
                    if (
                        existing is not None
                        and existing.unique_id != account.account_id
                    ):
                        return self.async_abort(reason="wrong_account")
                    await self.async_set_unique_id(account.account_id)
                    data = {
                        CONF_COOKIES: cookies,
                        CONF_TIMEZONE: timezone,
                        CONF_SOURCE_TIMEZONE: account.timezone,
                    }
                    if existing is not None:
                        updated = {**existing.data, **data}
                        return self.async_update_reload_and_abort(
                            existing,
                            data=updated,
                            options={**existing.options, CONF_TIMEZONE: timezone},
                            reason="reauth_successful"
                            if self.context.get("source") == "reauth"
                            else "reconfigure_successful",
                        )
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title="Lose It!", data=data)

        # Never echo submitted credentials or stash user_input on the flow object.
        fields: dict[Any, Any] = {}
        fields[vol.Required(CONF_SESSION)] = TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        )
        timezone_default = self.hass.config.time_zone
        if existing is not None:
            timezone_default = existing.options.get(
                CONF_TIMEZONE, existing.data.get(CONF_TIMEZONE, timezone_default)
            )
        fields[vol.Required(CONF_TIMEZONE, default=timezone_default)] = str
        return self.async_show_form(
            step_id="session",
            errors=errors,
            data_schema=vol.Schema(fields),
            description_placeholders={
                "website_url": "https://www.loseit.com/",
                "guide_url": "https://github.com/ColeMundus/ha-loseit/blob/main/docs/session-cookies.md",
            },
        )


class LoseItOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await async_valid_timezone(user_input[CONF_TIMEZONE])
            except vol.Invalid:
                errors[CONF_TIMEZONE] = "invalid_timezone"
            else:
                return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_MINUTES,
                        default=self.config_entry.options.get(
                            CONF_POLL_MINUTES, DEFAULT_POLL_MINUTES
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=1440)),
                    vol.Required(
                        CONF_TIMEZONE,
                        default=self.config_entry.options.get(
                            CONF_TIMEZONE, self.config_entry.data[CONF_TIMEZONE]
                        ),
                    ): str,
                }
            ),
        )
