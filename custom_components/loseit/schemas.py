"""Pinned source read layouts and array signatures; unknown types fail closed."""

from __future__ import annotations

from datetime import date

# Public first-party permutation and proxy policy observed 2026-11-05.
# These are build identifiers, never credentials. Server incompatibility fails closed.
PERMUTATION = "1E1F118F8C62ED7B7EE732414ECA543A"
POLICY = "F5AA51DFF7600BE94631854AFC5DEFE9"
EPOCH = date(2000, 12, 31)
MODULE_BASE = "https://d3hsih69yn4d89.cloudfront.net/web/"


# Domain read layouts adapted from phitoduck/lose-it.
# MIT License
#
# Copyright (c) 2026 phitoduck
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# Pinned source fabf4fd211b80e149015ef62a71d68c38a151264.
# Unknown signatures fail closed.
LAYOUTS: dict[str, str] = {
    # xEd instantiates from a long; wEd reads the nanosecond integer.
    "java.sql.Timestamp/3040052672": "li",
    "com.google.gwt.ajaxloader.client.Properties$TypeException/806639172": "s",
    "com.google.gwt.core.shared.SerializableThrowable/2791287161": "sboo",
    "com.google.gwt.event.shared.UmbrellaException/3104463596": "os",
    "com.google.gwt.http.client.RequestException/190587325": "s",
    "com.google.gwt.i18n.shared.impl.DateRecord/3173882066": "biiiiibiiiiii",
    "com.google.gwt.inject.client.multibindings.SimpleMultimap/2234506554": "ioo",
    "com.google.gwt.json.client.JSONException/2941795468": "s",
    "com.google.gwt.jsonp.client.TimeoutException/1112787596": "s",
    "com.google.gwt.safehtml.shared.SafeHtmlString/235635043": "s",
    "com.google.gwt.user.client.rpc.IncompatibleRemoteServiceException/3936916533": "s",
    "com.google.gwt.user.client.rpc.RpcTokenException/2345075298": "s",
    "com.google.gwt.user.client.rpc.SerializableException/3047383460": "s",
    "com.google.gwt.user.client.rpc.SerializationException/2836333220": "s",
    "com.google.gwt.user.client.rpc.SerializedTypeViolationException/914601580": "s",
    (
        "com.google.gwt.user.client.rpc."
        "ServiceDefTarget$NoServiceEntryPointSpecifiedException/3408313447"
    ): "s",
    "com.google.gwt.user.client.ui.ChangeListenerCollection/287642957": "io",
    "com.google.gwt.user.client.ui.ClickListenerCollection/2152455986": "io",
    "com.google.gwt.user.client.ui.FocusListenerCollection/119490835": "io",
    "com.google.gwt.user.client.ui.FormHandlerCollection/3088681894": "io",
    "com.google.gwt.user.client.ui.KeyboardListenerCollection/1040442242": "io",
    "com.google.gwt.user.client.ui.LoadListenerCollection/3174178888": "io",
    "com.google.gwt.user.client.ui.MouseListenerCollection/465158911": "io",
    "com.google.gwt.user.client.ui.MouseWheelListenerCollection/370304552": "io",
    "com.google.gwt.user.client.ui.PopupListenerCollection/1920131050": "io",
    "com.google.gwt.user.client.ui.ScrollListenerCollection/210686268": "io",
    "com.google.gwt.user.client.ui.TabListenerCollection/3768293299": "io",
    "com.google.gwt.user.client.ui.TableListenerCollection/2254740473": "io",
    "com.google.gwt.user.client.ui.TreeListenerCollection/3716243734": "io",
    (
        "com.google.gwt.useragent.client."
        "UserAgentAsserter$UserAgentAssertionError/1267019011"
    ): "s",
    "com.google.gwt.xml.client.impl.DOMParseException/3799120635": "sis",
    "com.google.web.bindery.event.shared.UmbrellaException/1025846929": "os",
    "com.loseit.core.client.application.ApplicationUnits/56862441": "doododododo",
    "com.loseit.core.client.helpers.StringConfiguration/3665392721": "ss",
    "com.loseit.core.client.model.AccountDetails/1131632329": "bsssoiso",
    "com.loseit.core.client.model.AccountSettings/63081682": "bs",
    "com.loseit.core.client.model.ActiveExercise/2291195331": "ioobiobiblo",
    "com.loseit.core.client.model.ActiveExerciseCategory/1493499494": "isoslo",
    "com.loseit.core.client.model.ActiveFood/640079221": "iooobibblo",
    "com.loseit.core.client.model.BMRSummary/4065403370": "didlood",
    "com.loseit.core.client.model.BasicChallengeDetails/2672607967": "sso",
    "com.loseit.core.client.model.BasicGroupDetails/1618295411": "sbsso",
    "com.loseit.core.client.model.CalorieBurnMetrics/3650191062": "odd",
    "com.loseit.core.client.model.Challenge/2299582057": "oosisibbiiisoiiiiiiooo",
    "com.loseit.core.client.model.ChallengeConfiguration/1288869657": "ss",
    "com.loseit.core.client.model.ChallengeLeader$ChallengeLeaderType/3156927838": "e",
    "com.loseit.core.client.model.ChallengeLeader/1451105523": "sossidoo",
    "com.loseit.core.client.model.ChallengeLocalization/231945978": "sssss",
    "com.loseit.core.client.model.ChallengeResults/2243877049": "bidiidio",
    "com.loseit.core.client.model.ChallengeType/2488299936": "e",
    "com.loseit.core.client.model.City/2457139280": "sisoss",
    "com.loseit.core.client.model.ConnectedEntity$ConnectedEntityType/2794522375": "e",
    "com.loseit.core.client.model.ConnectedEntity/3517880022": "oobsossssisss",
    "com.loseit.core.client.model.ConversationUserDetails/1389826723": "ssso",
    "com.loseit.core.client.model.CustomFood/327171432": "bbdiooobibblo",
    "com.loseit.core.client.model.CustomGoal/3094185758": "odbsooddsossooodslo",
    "com.loseit.core.client.model.CustomGoalMeasureFrequency/3968844069": "e",
    "com.loseit.core.client.model.CustomGoalType/3025174884": "e",
    "com.loseit.core.client.model.CustomGoalValue/1455343169": "ooboodlo",
    "com.loseit.core.client.model.DailyDetails/1565598417": "ooooooolooo",
    "com.loseit.core.client.model.DailyLogEntry/612926967": "ioddddol",
    "com.loseit.core.client.model.DailyLogEntryWithMeals/2444475740": "dddidioddddol",
    "com.loseit.core.client.model.DailyLogGoalsState/1324910267": "do",
    "com.loseit.core.client.model.DailySummary/2893279651": "oo",
    "com.loseit.core.client.model.Device/2727491380": "bsosssso",
    "com.loseit.core.client.model.EmailReportJobData/2315164848": "sbii",
    "com.loseit.core.client.model.EmailReportJobs/2139437073": "oooooo",
    "com.loseit.core.client.model.Exercise/768553247": "iisdsslo",
    "com.loseit.core.client.model.ExerciseCategory/2279150703": "ioisbsslo",
    "com.loseit.core.client.model.ExerciseCategoryI18N/2818558255": "boioisbsslo",
    "com.loseit.core.client.model.ExerciseCategoryLocaleOverride/1911762829": "osisslo",
    "com.loseit.core.client.model.ExerciseI18N/160268637": "boiisdsslo",
    "com.loseit.core.client.model.ExerciseLocaleOverride/528288820": "sossisblo",
    "com.loseit.core.client.model.ExerciseLogEntry/3129076305": "odoboobibiblo",
    (
        "com.loseit.core.client.model.ExtendedUserDetails/2147557844"
    ): "oosioooooosbsssoiso",
    "com.loseit.core.client.model.FoodForFoodDatabase/2501655516": "ooobbblii",
    "com.loseit.core.client.model.FoodIdentifier/2763145970": "issssoiolo",
    "com.loseit.core.client.model.FoodInsightDetailItem/1738289974": "dddiddssosddddi",
    "com.loseit.core.client.model.FoodLogEntry/264522954": "ooobllo",
    "com.loseit.core.client.model.FoodLogEntryContext/4082213671": "oobiiboooo",
    "com.loseit.core.client.model.FoodMeasure/1457474932": "e",
    "com.loseit.core.client.model.FoodNutrients/1097231324": "ddo",
    "com.loseit.core.client.model.FoodServing/1858865662": "oo",
    "com.loseit.core.client.model.FoodServingSize/63998910": "dboddd",
    "com.loseit.core.client.model.FriendPrivacyPolicy/2556698540": "oo",
    "com.loseit.core.client.model.FriendRequests/706891495": "ooo",
    "com.loseit.core.client.model.FriendsInitializationData/3216022052": "oo",
    "com.loseit.core.client.model.FriendsToShareWith/821023005": "oo",
    "com.loseit.core.client.model.GoalsData/340668567": "ooooo",
    "com.loseit.core.client.model.GoalsProfileGender/539918532": "e",
    "com.loseit.core.client.model.GoalsStatus/3937902525": "oo",
    "com.loseit.core.client.model.GoalsSummary$GoalsPlan/3474298027": "e",
    "com.loseit.core.client.model.GoalsSummary/907689655": "oobdoodooodbbdooooooodb",
    # Current ePg reader / gPg writer: p is a double, unlike the old schema.
    "com.loseit.core.client.model.GoalsSummary/26794011": "oobdoodooodbdooooooodb",
    "com.loseit.core.client.model.Group/1784714703": "oossosisosoo",
    "com.loseit.core.client.model.GroupDetails/117347956": "oooooossosisosoo",
    "com.loseit.core.client.model.GroupLocalization/2250983111": "ssssss",
    "com.loseit.core.client.model.GroupMembers/2659481073": "oo",
    "com.loseit.core.client.model.HourDate/83922329": "oi",
    "com.loseit.core.client.model.InitializationData/816563993": "ooooooso",
    "com.loseit.core.client.model.InitializationFriendsData/542454938": "ooo",
    "com.loseit.core.client.model.InsightPattern$InsightPatternType/2326390359": "e",
    "com.loseit.core.client.model.InsightPattern/2539910762": "oddiososio",
    "com.loseit.core.client.model.InsightPatternExternalResource/1168473427": "ss",
    (
        "com.loseit.core.client.model.InsightPatternSupplementalContent/2176461969"
    ): "sossssss",
    "com.loseit.core.client.model.InsightPatternsResponse/3381492235": "ooio",
    "com.loseit.core.client.model.IntegratedSystem/1801028358": "e",
    "com.loseit.core.client.model.InternalAccountDetails/691026731": "oosbsssoiso",
    "com.loseit.core.client.model.Invitation/536385869": "sossoss",
    "com.loseit.core.client.model.InviteContainer/2183478804": "ooo",
    "com.loseit.core.client.model.LogEntriesAndGoalsData/1494133653": "oo",
    "com.loseit.core.client.model.LogEntry/2095195315": "idddiiodd",
    "com.loseit.core.client.model.MotivatorData/954103295": "ooo",
    "com.loseit.core.client.model.MyFoodIdentifier/4176489858": "soos",
    "com.loseit.core.client.model.NewAccountCreationResult/2416032993": "e",
    "com.loseit.core.client.model.Note/3916765409": "sibisilo",
    "com.loseit.core.client.model.NotificationData/2585969803": "ooo",
    "com.loseit.core.client.model.NotificationLevel/4078218942": "e",
    "com.loseit.core.client.model.NotificationSettings/4225275760": "ss",
    "com.loseit.core.client.model.NutrientPreferences/1319652251": "bbbbbbbb",
    "com.loseit.core.client.model.NutrientSummary/3271902303": "oddoooddoodddd",
    "com.loseit.core.client.model.PopularEntry/2103893536": "disis",
    "com.loseit.core.client.model.Preferences/1976681881": "bssiobobbo",
    (
        "com.loseit.core.client.model.ProfileDetails/1071469966"
    ): "ooodooooododoosioooooosbsssoiso",
    "com.loseit.core.client.model.Recipe/643213359": "osobdsobsoooblo",
    "com.loseit.core.client.model.RecipeIngredient/3403312587": "booibiolo",
    "com.loseit.core.client.model.RecordedWeight/1309383152": "obld",
    "com.loseit.core.client.model.ReminderJobData$ReminderType/1420999111": "e",
    "com.loseit.core.client.model.ReminderJobData/1060897383": "iioi",
    "com.loseit.core.client.model.ReminderJobs/992842049": "oooooo",
    "com.loseit.core.client.model.SharedItem$SharedItemType/1200324739": "e",
    "com.loseit.core.client.model.SharedItem/3229011724": "issooisi",
    "com.loseit.core.client.model.SimplePrimaryKey/3621315060": "o",
    "com.loseit.core.client.model.SubscriptionDetails/510514359": "oob",
    "com.loseit.core.client.model.Team/1605656868": "ioossosisosoo",
    "com.loseit.core.client.model.TeamDetails/2497366650": "oooooooossosisosoo",
    "com.loseit.core.client.model.UnitTypeBloodGlucose/870205571": "e",
    "com.loseit.core.client.model.UnitTypeDistance/1938114904": "e",
    "com.loseit.core.client.model.UnitTypeEnergy/783891761": "e",
    "com.loseit.core.client.model.UnitTypeHeight/3122048970": "e",
    "com.loseit.core.client.model.UnitTypeLiquidVolume/484106684": "e",
    "com.loseit.core.client.model.UnitTypeWeight/3360017842": "e",
    "com.loseit.core.client.model.UserChallenge/2219552848": "oooosisibbiiisoiiiiiiooo",
    "com.loseit.core.client.model.UserDetails/4192519093": "ooosbsssoiso",
    "com.loseit.core.client.model.UserId/4281239478": "isi",
    "com.loseit.core.client.model.UserStatus/2206774507": "oodddd",
    "com.loseit.core.client.model.Version/837272391": "iiiis",
    "com.loseit.core.client.model.WeeklyDetails/3764412608": "oo",
    "com.loseit.core.client.model.WeeklySummary/1735863179": "oooooooo",
    (
        "com.loseit.core.client.model.activity.AchievementActivity/879150730"
    ): "oooiiisssooi",
    "com.loseit.core.client.model.activity.Activities/3700705398": "ooo",
    (
        "com.loseit.core.client.model.activity.ChallengeMessageActivity/3070871551"
    ): "oooiiisssooi",
    "com.loseit.core.client.model.activity.CommentActivity/1680192258": "oooiiisssooi",
    (
        "com.loseit.core.client.model.activity.ConversationActivity/3988320673"
    ): "ooosoooiiisssooi",
    "com.loseit.core.client.model.activity.ExerciseActivity/543106761": "oooiiisssooi",
    "com.loseit.core.client.model.activity.GoalActivity/3469248285": "oooiiisssooi",
    (
        "com.loseit.core.client.model.activity.GroupMessageActivity/3065920568"
    ): "oooiiisssooi",
    "com.loseit.core.client.model.activity.MessageActivity/3594426607": "oooiiisssooi",
    "com.loseit.core.client.model.activity.WeighInActivity/738371510": "oooiiisssooi",
    "com.loseit.core.client.model.budget.BudgetStateContext/1231009769": "ob",
    "com.loseit.core.client.model.budget.DailyBudget/2551066014": "oddodd",
    "com.loseit.core.client.model.budget.DailyBudgetContext/795512248": "oobd",
    "com.loseit.core.client.model.budget.DailyBudgetIdentifier/2427954186": "e",
    "com.loseit.core.client.model.budget.WeeklyBudgetContext/3975343574": "o",
    (
        "com.loseit.core.client.model.exceptions.ChallengeMaxLimitException/1630355280"
    ): "s",
    (
        "com.loseit.core.client.model.exceptions."
        "ChallengeTeamMaxLimitException/3923719384"
    ): "s",
    "com.loseit.core.client.model.integratedsystems.Capabilities/1178913253": "ss",
    "com.loseit.core.client.model.interfaces.FoodLogEntryType/1152459170": "e",
    "com.loseit.core.client.model.interfaces.FoodLogEntryTypeExtra/4048538730": "e",
    "com.loseit.core.client.model.interfaces.FoodProductType/2860616120": "e",
    "com.loseit.core.client.model.interfaces.GoalsProfileActivityLevel/3913803717": "e",
    "com.loseit.core.client.model.interfaces.NutritionStrategyType/707945675": "e",
    "com.loseit.core.client.model.payment.CardErrorException$Reason/3536192073": "e",
    "com.loseit.core.client.model.payment.CardErrorException/1182846405": "os",
    "com.loseit.core.client.model.payment.IntroductoryPeriodType/50258068": "e",
    "com.loseit.core.client.model.payment.PaymentCustomer/2152784070": "ooobs",
    "com.loseit.core.client.model.payment.Plan$Interval/1942828892": "e",
    "com.loseit.core.client.model.payment.Plan/3481011143": "obioioobssb",
    "com.loseit.core.client.model.payment.UserPaymentTransactionSource/3777837374": "e",
    "com.loseit.core.client.model.search.SearchResult/1043338856": "i",
    "com.loseit.core.client.model.search.SearchResultDialogActionType/1465237681": "e",
    "com.loseit.core.client.model.search.SearchResultExercise/4144849034": "osssiooi",
    "com.loseit.core.client.model.search.SearchResultFood/3343986608": "ossssoi",
    "com.loseit.core.client.model.search.SearchResultHeader/1305410512": "blosi",
    "com.loseit.core.client.model.search.SearchResultMeal/1893882416": "oosssi",
    "com.loseit.core.client.model.search.SearchResults/1258509077": "oi",
    "com.loseit.core.client.service.NewAccountCreationFailedException/233574200": "os",
    "com.loseit.core.client.service.UserAuthenticationFailedException/2362299878": "is",
    "com.loseit.core.client.service.responses.AddFriendResponse/2022374134": "si",
    (
        "com.loseit.core.client.service.responses."
        "LoseItRemoteServiceResponse/1071940969"
    ): "oolob",
    (
        "com.loseit.core.client.service.responses."
        "UnauthenticatedServiceResponse/2725618067"
    ): "lob",
    "com.loseit.core.client.service.responses.UpdateProfileResponse/227386058": "sii",
    "com.loseit.core.lava.model.app.App/4057627814": "e",
    "com.loseit.core.shared.exceptions.DisplayableUserException/1748904296": "sss",
    "com.loseit.core.shared.exceptions.NoPartitionException/1162340371": "s",
    "com.loseit.core.shared.exceptions.NokiaException/1702371333": "is",
    "com.loseit.core.shared.exceptions.NonloggingException/2560524743": "s",
    "com.loseit.core.shared.exceptions.PartitionOfflineException/1374732313": "sss",
    "com.loseit.core.shared.exceptions.PermissionDeniedException/2876868375": "s",
    "com.loseit.core.shared.exceptions.SystemMaintenanceException/3478816138": "s",
    "com.loseit.core.shared.landing.ChallengesLandingDescriptor/2837871445": "ooo",
    "com.loseit.core.shared.landing.ConfirmInfoLandingDescriptor/3145419265": "oo",
    (
        "com.loseit.core.shared.landing."
        "EligibilityLandingDescriptor$EligibilityFormat/2909519928"
    ): "e",
    "com.loseit.core.shared.landing.EligibilityLandingDescriptor/1638974938": "bosisso",
    "com.loseit.core.shared.landing.HintedLandingDescriptor$HintSet/3198251040": "osoi",
    "com.loseit.core.shared.landing.LandingContext$LandingContextType/3815039363": "e",
    "com.loseit.core.shared.landing.LandingContext/1194748876": "oooooooso",
    "com.loseit.core.shared.landing.LandingDescriptor/4085941921": "o",
    "com.loseit.core.shared.landing.LandingStepResult/2072004494": "ioo",
    "com.loseit.core.shared.landing.TermsLandingDescriptor/2475939776": "o",
    "com.loseit.core.shared.model.ClientApplicationContext/1459658406": "bo",
    "com.loseit.core.shared.model.DayDate/1611136587": "oii",
    "com.loseit.core.shared.model.DayOfWeek/736725074": "e",
    "com.loseit.core.shared.model.PrivacyPreferences/421687247": "oi",
    "com.loseit.core.shared.model.RelationshipValue/3067905684": "e",
    "com.loseit.core.shared.model.UserApplicationContext/3404477518": "oosboo",
    (
        "com.loseit.core.shared.model.connect.ExternalConnectProgram/3426893366"
    ): "iooisoos",
    "com.loseit.core.shared.model.connect.ProgramProperties/790624794": "ss",
    "com.loseit.core.shared.model.connect.ProgramType/4151848851": "e",
    "com.loseit.core.shared.model.conversations.Conversation/3738141544": "ooosoo",
    (
        "com.loseit.core.shared.model.invitations."
        "UserInvitationAlreadyClaimedException/311018182"
    ): "s",
    (
        "com.loseit.core.shared.model.invitations."
        "UserInvitationAlreadyUsedException/3628127033"
    ): "s",
    (
        "com.loseit.core.shared.model.invitations."
        "UserInvitationExpiredException/3693669771"
    ): "s",
    (
        "com.loseit.core.shared.model.invitations."
        "UserInvitationSentTooRecentlyException/2686976851"
    ): "s",
    (
        "com.loseit.healthdata.model.shared."
        "GwtSerializationDependencies$BrandDependencies/2442178065"
    ): "osooooo",
    "com.loseit.healthdata.model.shared.Verification/3485154600": "e",
    (
        "com.loseit.healthdata.model.shared.exception."
        "BrandDeletedImportException/1821590252"
    ): "oss",
    (
        "com.loseit.healthdata.model.shared.exception."
        "BrandNotFoundImportException/2049185062"
    ): "ooss",
    (
        "com.loseit.healthdata.model.shared.exception."
        "BrandNotLocalizedImportException/4067239006"
    ): "ooss",
    "com.loseit.healthdata.model.shared.exception.ImportException/3209422176": "ss",
    "com.loseit.healthdata.model.shared.food.Brand/3024558857": "sooooo",
    "com.loseit.healthdata.model.shared.food.BrandForLocale/2435789751": "sosooooo",
    "com.loseit.healthdata.model.shared.food.BrandId/2672631526": "s",
    "com.loseit.healthdata.model.shared.food.FoodMeasurement/2371921172": "e",
}

ARRAYS = frozenset(
    [
        "[B/3308590456",
        "[I/2970817851",
        "[Lcom.loseit.core.client.model.AccountDetails;/3192859924",
        "[Lcom.loseit.core.client.model.ActiveExercise;/4112181072",
        "[Lcom.loseit.core.client.model.ActiveExerciseCategory;/3948310042",
        "[Lcom.loseit.core.client.model.Challenge;/3743068782",
        "[Lcom.loseit.core.client.model.ChallengeLeader;/2380496464",
        "[Lcom.loseit.core.client.model.ChallengeLocalization;/3126610460",
        "[Lcom.loseit.core.client.model.City;/275360693",
        "[Lcom.loseit.core.client.model.ConnectedEntity;/3196022774",
        "[Lcom.loseit.core.client.model.ConversationUserDetails;/3715067389",
        "[Lcom.loseit.core.client.model.CustomFood;/3891990944",
        "[Lcom.loseit.core.client.model.CustomGoal;/4104812613",
        "[Lcom.loseit.core.client.model.CustomGoalValue;/3340358626",
        "[Lcom.loseit.core.client.model.DailyDetails;/2036651502",
        "[Lcom.loseit.core.client.model.DailyLogEntry;/2146499172",
        "[Lcom.loseit.core.client.model.DailyLogEntryWithMeals;/3034949036",
        "[Lcom.loseit.core.client.model.Device;/3566810925",
        "[Lcom.loseit.core.client.model.EmailReportJobData;/1964807568",
        "[Lcom.loseit.core.client.model.ExerciseCategoryLocaleOverride;/530206017",
        "[Lcom.loseit.core.client.model.ExerciseLocaleOverride;/31604535",
        "[Lcom.loseit.core.client.model.ExerciseLogEntry;/1448715428",
        "[Lcom.loseit.core.client.model.ExtendedUserDetails;/1773089271",
        "[Lcom.loseit.core.client.model.FoodForFoodDatabase;/3009199238",
        "[Lcom.loseit.core.client.model.FoodInsightDetailItem;/1458776255",
        "[Lcom.loseit.core.client.model.FoodLogEntry;/3918943916",
        "[Lcom.loseit.core.client.model.FoodServingSize;/810599869",
        "[Lcom.loseit.core.client.model.Group;/4020776143",
        "[Lcom.loseit.core.client.model.GroupDetails;/2816724428",
        "[Lcom.loseit.core.client.model.GroupLocalization;/1807972113",
        "[Lcom.loseit.core.client.model.InsightPattern;/3895548342",
        "[Lcom.loseit.core.client.model.IntegratedSystem;/2316922153",
        "[Lcom.loseit.core.client.model.InternalAccountDetails;/664848994",
        "[Lcom.loseit.core.client.model.Invitation;/217127847",
        "[Lcom.loseit.core.client.model.LogEntry;/105466560",
        "[Lcom.loseit.core.client.model.MyFoodIdentifier;/3672613004",
        "[Lcom.loseit.core.client.model.Note;/2857659498",
        "[Lcom.loseit.core.client.model.NutrientSummary;/2824137653",
        "[Lcom.loseit.core.client.model.PopularEntry;/216212859",
        "[Lcom.loseit.core.client.model.ProfileDetails;/208950177",
        "[Lcom.loseit.core.client.model.Recipe;/246827078",
        "[Lcom.loseit.core.client.model.RecipeIngredient;/2059606128",
        "[Lcom.loseit.core.client.model.RecordedWeight;/503475614",
        "[Lcom.loseit.core.client.model.ReminderJobData;/1047339722",
        "[Lcom.loseit.core.client.model.SharedItem;/3737107063",
        "[Lcom.loseit.core.client.model.SimplePrimaryKey;/995428388",
        "[Lcom.loseit.core.client.model.Team;/1007853726",
        "[Lcom.loseit.core.client.model.TeamDetails;/2783239976",
        "[Lcom.loseit.core.client.model.UserChallenge;/62776769",
        "[Lcom.loseit.core.client.model.UserDetails;/3342858499",
        "[Lcom.loseit.core.client.model.activity.AchievementActivity;/3674177494",
        "[Lcom.loseit.core.client.model.activity.Activity;/1029547820",
        "[Lcom.loseit.core.client.model.activity.ChallengeMessageActivity;/3933961534",
        "[Lcom.loseit.core.client.model.activity.CommentActivity;/1805863315",
        "[Lcom.loseit.core.client.model.activity.ConversationActivity;/1339610487",
        "[Lcom.loseit.core.client.model.activity.ExerciseActivity;/1854627422",
        "[Lcom.loseit.core.client.model.activity.GoalActivity;/4169300991",
        "[Lcom.loseit.core.client.model.activity.GroupMessageActivity;/2101678362",
        "[Lcom.loseit.core.client.model.activity.MessageActivity;/2151147214",
        "[Lcom.loseit.core.client.model.activity.UserActivity;/3697812154",
        "[Lcom.loseit.core.client.model.activity.WeighInActivity;/690250147",
        "[Lcom.loseit.core.client.model.budget.DailyBudgetContext;/32223838",
        "[Lcom.loseit.core.client.model.interfaces.ILogEntry;/2338671867",
        "[Lcom.loseit.core.client.model.interfaces.ILogEntryWithPending;/2549867056",
        "[Lcom.loseit.core.client.model.interfaces.IPrimaryKey;/2835828912",
        "[Lcom.loseit.core.client.model.interfaces.SearchableUserDetails;/2103144036",
        "[Lcom.loseit.core.client.model.search.SearchResult;/1298022602",
        "[Lcom.loseit.core.client.model.search.SearchResultExercise;/781409772",
        "[Lcom.loseit.core.client.model.search.SearchResultFood;/1670943319",
        "[Lcom.loseit.core.client.model.search.SearchResultHeader;/2374251150",
        "[Lcom.loseit.core.client.model.search.SearchResultMeal;/4217720383",
        "[Lcom.loseit.core.client.service.responses.AddFriendResponse;/2940537098",
        "[Lcom.loseit.core.shared.landing.HintedLandingDescriptor$HintSet;/3109587479",
        "[Lcom.loseit.core.shared.model.ClientApplicationContext;/996892391",
        "[Lcom.loseit.core.shared.model.connect.ExternalConnectProgram;/4203474425",
        "[Lcom.loseit.core.shared.model.conversations.Conversation;/457233624",
        "[Ljava.lang.Double;/2857560407",
        "[Ljava.lang.Integer;/1574882222",
        "[Ljava.lang.StackTraceElement;/3867167983",
        "[Ljava.lang.String;/2600011424",
    ]
)
