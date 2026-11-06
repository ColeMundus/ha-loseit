"""Remote release identity checks use synthetic gh responses, never the network."""

import json
import subprocess

import pytest

from scripts import verify_release_tag as verifier

COMMIT = "a" * 40
OTHER = "b" * 40
TAG_SHA = "c" * 40
NESTED = "d" * 40
REPO = "example/integration"
TAG = "v1.2.3"


def git_object(kind="commit", sha=COMMIT):
    return {"type": kind, "sha": sha}


def ref(obj=None):
    return {"ref": f"refs/tags/{TAG}", "object": obj or git_object()}


@pytest.fixture
def gh(monkeypatch):
    calls = []
    responses = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        assert argv[:5] == ["gh", "api", "--method", "GET", "--hostname"]
        assert argv[5] == "github.com"
        assert kwargs == {
            "check": True,
            "capture_output": True,
            "text": True,
            "timeout": 30,
        }
        assert responses, "Unexpected API request"
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(response))

    monkeypatch.setattr(verifier.subprocess, "run", run)
    return responses, calls


def test_lightweight_tag(gh):
    responses, calls = gh
    responses.append(ref())
    assert verifier.verify_release_tag(REPO, TAG, COMMIT) == COMMIT
    assert calls[0][0][-1] == f"repos/{REPO}/git/ref/tags/{TAG}"
    assert not responses


def test_nested_annotated_tags(gh):
    responses, calls = gh
    responses.extend(
        [
            ref(git_object("tag", TAG_SHA)),
            {"sha": TAG_SHA, "object": git_object("tag", NESTED)},
            {"sha": NESTED, "object": git_object()},
        ]
    )
    assert verifier.verify_release_tag(REPO, TAG, COMMIT) == COMMIT
    assert [call[0][-1] for call in calls[1:]] == [
        f"repos/{REPO}/git/tags/{TAG_SHA}",
        f"repos/{REPO}/git/tags/{NESTED}",
    ]


@pytest.mark.parametrize("annotated", [False, True])
def test_moved_tag_fails(gh, annotated):
    responses, _ = gh
    responses.extend(
        [
            ref(git_object("tag", TAG_SHA)),
            {"sha": TAG_SHA, "object": git_object(sha=OTHER)},
        ]
        if annotated
        else [ref(git_object(sha=OTHER))]
    )
    with pytest.raises(ValueError, match="does not match"):
        verifier.verify_release_tag(REPO, TAG, COMMIT)


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, "gh", stderr="404 tag missing"),
        subprocess.CalledProcessError(1, "gh", stderr="403 forbidden"),
        subprocess.TimeoutExpired("gh", 30),
        FileNotFoundError("gh"),
    ],
)
@pytest.mark.parametrize("annotated", [False, True])
def test_lookup_errors_fail_closed(gh, error, annotated):
    responses, _ = gh
    if annotated:
        responses.append(ref(git_object("tag", TAG_SHA)))
    responses.append(error)
    with pytest.raises(ValueError, match="lookup failed"):
        verifier.verify_release_tag(REPO, TAG, COMMIT)


@pytest.mark.parametrize(
    "response",
    [
        None,
        [],
        "unexpected",
        {},
        {"message": "Not Found"},
        {"ref": "refs/tags/other", "object": git_object()},
        {"ref": f"refs/tags/{TAG}", "object": None},
        ref({"sha": COMMIT}),
        ref({"type": "commit"}),
        ref(git_object("tree")),
        ref(git_object("blob")),
        ref(git_object([], COMMIT)),
        ref(git_object(sha=123)),
        ref(git_object(sha="a" * 39)),
        ref(git_object(sha="g" * 40)),
        ref(git_object(sha=COMMIT + "\n")),
    ],
)
def test_malformed_ref_rejected(gh, response):
    gh[0].append(response)
    with pytest.raises(ValueError):
        verifier.verify_release_tag(REPO, TAG, COMMIT)


@pytest.mark.parametrize(
    "response",
    [
        None,
        [],
        {},
        {"sha": TAG_SHA},
        {"sha": OTHER, "object": git_object()},
        {"sha": TAG_SHA, "object": git_object("tree")},
        {"sha": TAG_SHA, "object": git_object(sha=False)},
    ],
)
def test_malformed_annotated_tag_rejected(gh, response):
    gh[0].extend([ref(git_object("tag", TAG_SHA)), response])
    with pytest.raises(ValueError):
        verifier.verify_release_tag(REPO, TAG, COMMIT)


def test_invalid_json_rejected(monkeypatch):
    monkeypatch.setattr(
        verifier.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess([], 0, stdout="not json"),
    )
    with pytest.raises(ValueError, match="lookup failed"):
        verifier.verify_release_tag(REPO, TAG, COMMIT)


def test_annotation_loop_rejected(gh):
    responses, calls = gh
    responses.extend(
        [
            ref(git_object("tag", TAG_SHA)),
            {"sha": TAG_SHA, "object": git_object("tag", NESTED)},
            {"sha": NESTED, "object": git_object("tag", TAG_SHA)},
        ]
    )
    with pytest.raises(ValueError, match="cycle"):
        verifier.verify_release_tag(REPO, TAG, COMMIT)
    assert len(calls) == 3


def test_annotation_depth_bounded(gh):
    responses, calls = gh
    shas = [f"{n:040x}" for n in range(verifier.MAX_TAG_DEPTH + 1)]
    responses.append(ref(git_object("tag", shas[0])))
    responses.extend(
        {"sha": sha, "object": git_object("tag", next_sha)}
        for sha, next_sha in zip(shas, shas[1:], strict=False)
    )
    with pytest.raises(ValueError, match="depth"):
        verifier.verify_release_tag(REPO, TAG, COMMIT)
    assert len(calls) == verifier.MAX_TAG_DEPTH + 1


@pytest.mark.parametrize("sha", ["", "main", "a" * 39, "g" * 40, COMMIT + "\n", None])
def test_bad_expected_sha_never_queries(gh, sha):
    with pytest.raises(ValueError):
        verifier.verify_release_tag(REPO, TAG, sha)
    assert not gh[1]


@pytest.mark.parametrize(
    ("repo", "tag"),
    [
        ("https://example.test/repo", TAG),
        ("../repo", TAG),
        (REPO, ""),
        (REPO, "v1\n.2.3"),
    ],
)
def test_bad_inputs_never_query(gh, repo, tag):
    with pytest.raises(ValueError):
        verifier.verify_release_tag(repo, tag, COMMIT)
    assert not gh[1]


def test_tag_is_encoded_not_interpolated(gh):
    tag = "release/$(touch nope)"
    gh[0].append({"ref": f"refs/tags/{tag}", "object": git_object()})
    verifier.verify_release_tag(REPO, tag, COMMIT)
    assert gh[1][0][0][-1].endswith("release%2F%24%28touch%20nope%29")


def test_cli_fails_closed_and_success(monkeypatch, gh, capsys):
    monkeypatch.setenv("GH_REPO", REPO)
    monkeypatch.setenv("TAG", TAG)
    monkeypatch.setenv("EXPECTED_SHA", COMMIT)
    gh[0].append(ref(git_object(sha=OTHER)))
    with pytest.raises(SystemExit) as error:
        verifier.main()
    assert error.value.code == 1
    assert "does not match" in capsys.readouterr().err
    gh[0].append(ref())
    verifier.main()
    assert COMMIT in capsys.readouterr().out
    monkeypatch.delenv("EXPECTED_SHA")
    with pytest.raises(SystemExit) as error:
        verifier.main()
    assert error.value.code == 1
