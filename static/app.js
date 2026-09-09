// ============================================================
// GATEBALL LOVERS
// Main JavaScript
// ============================================================


// ============================================================
// SUPABASE CONNECTION
// ============================================================

const SUPABASE_URL =
    "https://cxogmmfohegychxwadqv.supabase.co";

// IMPORTANT:
// Keep your existing Supabase Publishable Key here.
// DO NOT use a service_role or secret key.

const SUPABASE_PUBLISHABLE_KEY =
    "sb_publishable_V-ID9zcQ7PrdOfQSyWNq_A_Hr5WKtr1";


const supabaseClient =
    window.supabase.createClient(
        SUPABASE_URL,
        SUPABASE_PUBLISHABLE_KEY
    );


console.log(
    "Gateball Lovers Supabase client created."
);


// ============================================================
// COMMON HELPERS
// ============================================================

function getElement(id) {

    return document.getElementById(id);

}


function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


function formatDate(dateValue) {

    if (!dateValue) {
        return "";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
        return dateValue;
    }

    return date.toLocaleDateString(
        undefined,
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );

}


// ============================================================
// LOGIN
// ============================================================

const loginForm =
    getElement("loginForm");


if (loginForm) {

    loginForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const email =
                getElement("email").value.trim();

            const password =
                getElement("password").value;


            if (!email || !password) {

                alert(
                    "Please enter your email and password."
                );

                return;
            }


            const loginButton =
                loginForm.querySelector(
                    ".login-button"
                );


            loginButton.disabled = true;
            loginButton.textContent =
                "Logging in...";


            try {

                const {
                    data,
                    error
                } =
                    await supabaseClient.auth
                        .signInWithPassword({
                            email: email,
                            password: password
                        });


                if (error) {
                    throw error;
                }


                console.log(
                    "Login successful:",
                    data
                );


                const userId =
                    data.user.id;


                // ------------------------------------------------
                // LOAD PROFILE
                // ------------------------------------------------

                const {
                    data: profile,
                    error: profileError
                } =
                    await supabaseClient
                        .from("profiles")
                        .select(
                            "id, full_name, email, role, country, phone, photo_url"
                        )
                        .eq("id", userId)
                        .single();


                if (profileError) {

                    console.error(
                        "Profile loading error:",
                        profileError
                    );

                }


                console.log(
                    "Gateball profile:",
                    profile
                );

currentUserId = userId;

currentUserProfile = profile || {
    id: userId,
    full_name: email.split("@")[0],
    email: email,
    role: "Player"
};

                // ------------------------------------------------
                // SHOW DASHBOARD
                // ------------------------------------------------

                getElement(
                    "loginScreen"
                ).style.display = "none";


                getElement(
                    "dashboardScreen"
                ).style.display = "block";


                getElement(
                    "bottomNav"
                ).style.display = "grid";


                const userName =
                    profile?.full_name ||
                    email.split("@")[0];


                const userRole =
                    profile?.role ||
                    "Player";


                getElement(
                    "dashboardWelcome"
                ).textContent =
                    "Welcome, " + userName + "!";


                getElement(
                    "dashboardRole"
                ).textContent =
                    "Role: " + userRole;


                // ------------------------------------------------
                // LOAD COMPLETE DASHBOARD
                // ------------------------------------------------

                await loadDashboard();


            } catch (error) {

                console.error(
                    "Login error:",
                    error
                );


                alert(
                    "Login failed:\n\n" +
                    (
                        error.message ||
                        "Unknown error"
                    )
                );


            } finally {

                loginButton.disabled = false;

                loginButton.textContent =
                    "LOGIN";

            }

        }
    );

}


// ============================================================
// LOAD COMPLETE DASHBOARD
// ============================================================

async function loadDashboard() {

    console.log(
        "Loading complete dashboard..."
    );


    await Promise.allSettled([

        loadCommunityCounts(),

        loadTournamentCount(),

        loadLiveMatchCount(),

        loadUpcomingTournaments(),

        loadLiveMatches(),

        loadGateballNews(),

        loadMessageBoard()

    ]);


    console.log(
        "Dashboard loading completed."
    );

}


// ============================================================
// COMMUNITY COUNTS
// ============================================================

async function loadCommunityCounts() {

    try {

        const {
            data,
            error
        } =
            await supabaseClient
                .from("community_profiles")
                .select("id, role");


        if (error) {
            throw error;
        }


        const members =
            data || [];


        const players =
            members.filter(
                member =>
                    (member.role || "")
                        .trim()
                        .toLowerCase()
                    === "player"
            ).length;


        const organizers =
            members.filter(
                member =>
                    (member.role || "")
                        .trim()
                        .toLowerCase()
                    === "organizer"
            ).length;


        getElement(
            "playersCount"
        ).textContent =
            players;


        getElement(
            "organizersCount"
        ).textContent =
            organizers;


        console.log(
            "Community counts:",
            players,
            "players,",
            organizers,
            "organizers"
        );


    } catch (error) {

        console.error(
            "Could not load community counts:",
            error
        );

    }

}


// ============================================================
// TOTAL TOURNAMENT COUNT
// ============================================================

async function loadTournamentCount() {

    try {

        const {
            data,
            error
        } =
            await supabaseClient
                .from("tournaments")
                .select("id");


        if (error) {
            throw error;
        }


        const count =
            (data || []).length;


        getElement(
            "tournamentsCount"
        ).textContent =
            count;


        console.log(
            "Tournament count:",
            count
        );


    } catch (error) {

        console.error(
            "Could not load tournament count:",
            error
        );

    }

}


// ============================================================
// LIVE MATCH COUNT
// ============================================================

async function loadLiveMatchCount() {

    try {

        const {
            data,
            error
        } =
            await supabaseClient
                .from("tournaments")
                .select(
                    "id, status, live_link"
                )
                .eq(
                    "status",
                    "Ongoing"
                );


        if (error) {
            throw error;
        }


        const liveMatches =
            (data || []).filter(
                tournament =>
                    tournament.live_link
            ).length;


        getElement(
            "liveMatchesCount"
        ).textContent =
            liveMatches;


        console.log(
            "Live matches:",
            liveMatches
        );


    } catch (error) {

        console.error(
            "Could not load live match count:",
            error
        );

    }

}


// ============================================================
// UPCOMING TOURNAMENTS
// ============================================================

async function loadUpcomingTournaments() {

    const container =
        getElement(
            "upcomingTournaments"
        );


    if (!container) {
        return;
    }


    container.innerHTML =
        `
        <div class="empty-message">
            Loading tournaments...
        </div>
        `;


    try {

        const today =
            new Date()
                .toISOString()
                .split("T")[0];


        const {
            data,
            error
        } =
            await supabaseClient
                .from("tournaments")
                .select(
                    "id, name, venue, country, event_type, start_date, end_date, description, status, live_link"
                )
                .gte(
                    "end_date",
                    today
                )
                .order(
                    "start_date",
                    {
                        ascending: true
                    }
                )
                .limit(10);


        if (error) {
            throw error;
        }


        const tournaments =
            data || [];


        if (tournaments.length === 0) {

            container.innerHTML =
                `
                <div class="empty-message">
                    No upcoming tournaments found.
                </div>
                `;

            return;
        }


        container.innerHTML =
            tournaments
                .map(
                    tournament => {

                        const name =
                            escapeHtml(
                                tournament.name ||
                                "Gateball Tournament"
                            );


                        const venue =
                            escapeHtml(
                                tournament.venue ||
                                "Venue not specified"
                            );


                        const country =
                            escapeHtml(
                                tournament.country ||
                                ""
                            );


                        const eventType =
                            escapeHtml(
                                tournament.event_type ||
                                ""
                            );


                        const status =
                            escapeHtml(
                                tournament.status ||
                                "Upcoming"
                            );


                        return `
                        <div class="tournament-card">

                            <div class="tournament-name">
                                🏆 ${name}
                            </div>

                            <div class="tournament-info">

                                📅
                                ${formatDate(tournament.start_date)}

                                ${
                                    tournament.end_date
                                    ?
                                    " — " +
                                    formatDate(
                                        tournament.end_date
                                    )
                                    :
                                    ""
                                }

                                <br>

                                📍 ${venue}

                                ${
                                    country
                                    ?
                                    "<br>🌏 " +
                                    country
                                    :
                                    ""
                                }

                                ${
                                    eventType
                                    ?
                                    "<br>🎯 " +
                                    eventType
                                    :
                                    ""
                                }

                            </div>

                            <span class="status-badge">
                                ${status}
                            </span>

                        </div>
                        `;

                    }
                )
                .join("");


    } catch (error) {

        console.error(
            "Could not load upcoming tournaments:",
            error
        );


        container.innerHTML =
            `
            <div class="empty-message">
                Unable to load upcoming tournaments.
            </div>
            `;

    }

}


// ============================================================
// LIVE MATCHES LIST
// ============================================================

async function loadLiveMatches() {

    const container =
        getElement(
            "liveMatchesList"
        );


    if (!container) {
        return;
    }


    try {

        const {
            data,
            error
        } =
            await supabaseClient
                .from("tournaments")
                .select(
                    "id, name, venue, country, event_type, start_date, end_date, status, live_link"
                )
                .eq(
                    "status",
                    "Ongoing"
                )
                .order(
                    "start_date",
                    {
                        ascending: true
                    }
                );


        if (error) {
            throw error;
        }


        const matches =
            (data || []).filter(
                tournament =>
                    tournament.live_link
            );


        if (matches.length === 0) {

            container.innerHTML =
                `
                <div class="empty-message">
                    No live matches at the moment.
                </div>
                `;

            return;
        }


        container.innerHTML =
            matches
                .map(
                    tournament => {

                        const name =
                            escapeHtml(
                                tournament.name ||
                                "Live Gateball Match"
                            );


                        const venue =
                            escapeHtml(
                                tournament.venue ||
                                "Venue not specified"
                            );


                        return `
                        <div class="tournament-card">

                            <div class="tournament-name">
                                🔴 ${name}
                            </div>

                            <div class="tournament-info">

                                📍 ${venue}

                                ${
                                    tournament.country
                                    ?
                                    "<br>🌏 " +
                                    escapeHtml(
                                        tournament.country
                                    )
                                    :
                                    ""
                                }

                            </div>

                            <span class="status-badge live-badge">
                                🔴 LIVE NOW
                            </span>

                            <br>

                            <a
                                class="live-link"
                                href="${escapeHtml(tournament.live_link)}"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                ▶ Watch Live
                            </a>

                        </div>
                        `;

                    }
                )
                .join("");


    } catch (error) {

        console.error(
            "Could not load live matches:",
            error
        );


        container.innerHTML =
            `
            <div class="empty-message">
                No live matches available.
            </div>
            `;

    }

}


// ============================================================
// GATEBALL NEWS
// ============================================================

async function loadGateballNews() {

    const container =
        getElement(
            "newsList"
        );


    if (!container) {
        return;
    }


    /*
        We intentionally keep this section independent
        from Supabase so the dashboard can display news
        even when no news table has been created yet.

        These are official Gateball organization websites.
    */


    const newsItems = [

        {
            title:
                "World Gateball Union — Official News",

            source:
                "World Gateball Union",

            url:
                "https://gateball.or.jp/"
        },

        {
            title:
                "Japan Gateball Union — Official Information",

            source:
                "Japan Gateball Union",

            url:
                "https://gateball.or.jp/"
        }

    ];


    container.innerHTML =
        newsItems
            .map(
                item => `

                <div class="news-card">

                    <div class="news-title">
                        📰 ${escapeHtml(item.title)}
                    </div>

                    <div class="news-source">
                        ${escapeHtml(item.source)}
                    </div>

                    <a
                        class="news-link"
                        href="${escapeHtml(item.url)}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Read Official Information →
                    </a>

                </div>

                `
            )
            .join("");

}


// ============================================================
// MESSAGE BOARD
// ============================================================

async function loadMessageBoard() {

    const container =
        getElement(
            "messageBoard"
        );


    if (!container) {
        return;
    }


    /*
        The exact message-board table was not part of the
        confirmed web dashboard schema yet.

        Therefore we do NOT query a guessed table name.
        This prevents unnecessary Supabase errors.

        We will connect this section to your actual
        Message Board table in the next Dashboard phase.
    */


    container.innerHTML =
        `

        <div class="message-card">

            <div class="message-title">
                📢 Gateball Lovers Community
            </div>

            <div class="message-text">
                Welcome to the Gateball Lovers community.
                Tournament announcements, important
                community messages and organizer updates
                will appear here.
            </div>

            <div class="message-date">
                Gateball Lovers
            </div>

        </div>

        `;

}


// ============================================================
// REFRESH DASHBOARD
// ============================================================

const refreshButton =
    getElement(
        "refreshButton"
    );


if (refreshButton) {

    refreshButton.addEventListener(
        "click",
        async function () {

            refreshButton.disabled = true;

            refreshButton.textContent =
                "Loading...";


            try {

                await loadDashboard();

            } finally {

                refreshButton.disabled = false;

                refreshButton.textContent =
                    "Refresh";

            }

        }
    );

}


// ============================================================
// LOGOUT
// ============================================================

const logoutButton =
    getElement(
        "logoutButton"
    );


if (logoutButton) {

    logoutButton.addEventListener(
        "click",
        async function () {

            try {

                const {
                    error
                } =
                    await supabaseClient.auth
                        .signOut();


                if (error) {
                    throw error;
                }


            } catch (error) {

                console.error(
                    "Logout error:",
                    error
                );

            }


            getElement(
                "dashboardScreen"
            ).style.display = "none";


            getElement(
                "bottomNav"
            ).style.display = "none";


            getElement(
                "loginScreen"
            ).style.display = "flex";


            getElement(
                "password"
            ).value = "";
currentUserId = null;
currentUserProfile = null;

tournamentCache = [];
tournamentJoinedMap = {};
tournamentResultCache = {};
        }
    );

}


// ============================================================
// BOTTOM NAVIGATION
// ============================================================

const navButtons =
    document.querySelectorAll(
        ".nav-button"
    );

navButtons.forEach(
    button => {

        button.addEventListener(
            "click",
            async function () {

                navButtons.forEach(
                    item =>
                        item.classList.remove(
                            "active"
                        )
                );

                this.classList.add(
                    "active"
                );

                const section =
                    this.dataset.section;

                console.log(
                    "Navigation selected:",
                    section
                );

                // ------------------------------------------------
                // HOME
                // ------------------------------------------------

                if (
                    section === "home"
                ) {

                    const dashboardScreen =
                        getElement(
                            "dashboardScreen"
                        );

                    const tournamentScreen =
                        getElement(
                            "tournamentScreen"
                        );

                    if (dashboardScreen) {
                        dashboardScreen.style.display =
                            "block";
                    }

                    if (tournamentScreen) {
                        tournamentScreen.style.display =
                            "none";
                    }

                    window.scrollTo({
                        top: 0,
                        behavior: "smooth"
                    });

                    return;
                }


                // ------------------------------------------------
                // TOURNAMENTS
                // ------------------------------------------------

                if (
                    section === "tournaments"
                ) {

                    const dashboardScreen =
                        getElement(
                            "dashboardScreen"
                        );

                    const tournamentScreen =
                        getElement(
                            "tournamentScreen"
                        );

                    if (dashboardScreen) {
                        dashboardScreen.style.display =
                            "none";
                    }

                    if (tournamentScreen) {
                        tournamentScreen.style.display =
                            "block";
                    }

                    await loadTournamentPage();

                    return;
                }


                // ------------------------------------------------
                // CHAT
                // ------------------------------------------------

                if (
                    section === "chat"
                ) {

                    alert(
                        "Chat section is coming next."
                    );

                    return;
                }


                // ------------------------------------------------
                // PROFILE
                // ------------------------------------------------

                if (
                    section === "profile"
                ) {

                    alert(
                        "Profile section is coming next."
                    );

                    return;
                }

            }
        );

    }
);


// ============================================================
// CHECK EXISTING SESSION
// ============================================================

async function checkExistingSession() {

    try {

        const {
            data,
            error
        } =
            await supabaseClient.auth
                .getSession();


        if (error) {
            throw error;
        }


        const session =
            data?.session;


        if (!session) {

            console.log(
                "No existing Supabase session."
            );

            return;
        }


        console.log(
            "Existing Supabase session found."
        );


        const userId =
            session.user.id;
currentUserId = userId;

currentUserProfile = profile || {
    id: userId,
    full_name:
        session.user.email.split("@")[0],
    email:
        session.user.email,
    role:
        "Player"
};

        const {
            data: profile,
            error: profileError
        } =
            await supabaseClient
                .from("profiles")
                .select(
                    "id, full_name, email, role, country, phone, photo_url"
                )
                .eq(
                    "id",
                    userId
                )
                .single();


        if (profileError) {

            console.error(
                "Existing profile error:",
                profileError
            );

        }
currentUserId = userId;

currentUserProfile = profile || {
    id: userId,
    full_name:
        session.user.email.split("@")[0],
    email:
        session.user.email,
    role:
        "Player"
};

        getElement(
            "loginScreen"
        ).style.display = "none";


        getElement(
            "dashboardScreen"
        ).style.display = "block";


        getElement(
            "bottomNav"
        ).style.display = "grid";


        const userName =
            profile?.full_name ||
            session.user.email
                .split("@")[0];


        const userRole =
            profile?.role ||
            "Player";


        getElement(
            "dashboardWelcome"
        ).textContent =
            "Welcome, " + userName + "!";


        getElement(
            "dashboardRole"
        ).textContent =
            "Role: " + userRole;


        await loadDashboard();


    } catch (error) {

        console.error(
            "Session check error:",
            error
        );

    }

}

// ============================================================
// TOURNAMENT SYSTEM
// ============================================================

let currentUserId = null;
let currentUserProfile = null;

let tournamentCache = [];
let tournamentJoinedMap = {};
let tournamentResultCache = {};

let currentTournamentTab = "Upcoming";


// ============================================================
// HELPERS
// ============================================================

function normalizedRole() {

    return (
        currentUserProfile?.role ||
        "Player"
    )
        .trim()
        .toLowerCase();

}


function canManageTournaments() {

    const role =
        normalizedRole();

    return (
        role === "admin" ||
        role === "organizer"
    );

}


function isPlayer() {

    return (
        normalizedRole() === "player"
    );

}


function safeUrl(value) {

    if (!value) {
        return "";
    }

    try {

        const url =
            new URL(value);

        if (
            url.protocol === "http:" ||
            url.protocol === "https:"
        ) {
            return url.href;
        }

    } catch (error) {

        console.error(
            "Invalid URL:",
            error
        );

    }

    return "";

}


function tournamentStatusFromDates(
    startDate,
    endDate
) {

    const today =
        new Date()
            .toISOString()
            .split("T")[0];

    if (today < startDate) {
        return "Upcoming";
    }

    if (today > endDate) {
        return "Finished";
    }

    return "Ongoing";

}


function getPositionLabel(position) {

    if (Number(position) === 1) {
        return "🥇 1st";
    }

    if (Number(position) === 2) {
        return "🥈 2nd";
    }

    if (Number(position) === 3) {
        return "🥉 3rd";
    }

    if (Number(position) === 4) {
        return "🏅 4th";
    }

    return position + "th";

}


function showModal(id) {

    const modal =
        getElement(id);

    if (!modal) {
        return;
    }

    modal.style.display =
        "flex";

}


function hideModal(id) {

    const modal =
        getElement(id);

    if (!modal) {
        return;
    }

    modal.style.display =
        "none";

}


// ============================================================
// OPEN TOURNAMENT PAGE
// ============================================================

async function loadTournamentPage() {

    console.log(
        "======================================"
    );

    console.log(
        "LOADING TOURNAMENT PAGE"
    );

    console.log(
        "Current tab:",
        currentTournamentTab
    );

    console.log(
        "Current user:",
        currentUserId
    );

    console.log(
        "Current profile:",
        currentUserProfile
    );

    console.log(
        "======================================"
    );


    const tournamentScreen =
        getElement(
            "tournamentScreen"
        );

    if (!tournamentScreen) {

        console.error(
            "ERROR: tournamentScreen does not exist in index.html"
        );

        alert(
            "Tournament screen is missing from index.html."
        );

        return;

    }


    const list =
        getElement(
            "tournamentList"
        );

    if (!list) {

        console.error(
            "ERROR: tournamentList does not exist in index.html"
        );

        alert(
            "Tournament list area is missing from index.html."
        );

        return;

    }


    list.innerHTML =
        `
        <div class="empty-message">
            Loading ${currentTournamentTab} tournaments...
        </div>
        `;


    try {

        // =====================================================
        // PULL ALL TOURNAMENTS FROM SUPABASE
        // =====================================================

        const {
            data,
            error
        } =
            await supabaseClient
                .from("tournaments")
                .select(
                    `
                    id,
                    name,
                    venue,
                    event_type,
                    start_date,
                    end_date,
                    organizer_id,
                    organizer_name,
                    status,
                    country,
                    description,
                    updated_at,
                    live_link,
                    created_at
                    `
                )
                .order(
                    "start_date",
                    {
                        ascending: true
                    }
                );


        if (error) {

            console.error(
                "SUPABASE TOURNAMENT ERROR:",
                error
            );

            throw error;

        }


        tournamentCache =
            data || [];


        console.log(
            "Total tournaments pulled from Supabase:",
            tournamentCache.length
        );


        // =====================================================
        // LOAD JOINED PLAYERS
        // =====================================================

        await loadTournamentPlayers();


        // =====================================================
        // LOAD RESULTS
        // =====================================================

        await loadTournamentResults();


        // =====================================================
        // SHOW CORRECT TAB
        // =====================================================

        renderTournamentTabs();

        renderTournamentList();


    } catch (error) {

        console.error(
            "TOURNAMENT PAGE ERROR:",
            error
        );


        list.innerHTML =
            `
            <div class="empty-message">

                <strong>
                    Unable to load tournaments.
                </strong>

                <br><br>

                ${escapeHtml(
                    error.message ||
                    "Unknown Supabase error"
                )}

            </div>
            `;

    }

}


// ============================================================
// LOAD JOINED PLAYERS
// ============================================================

async function loadTournamentPlayers() {

    tournamentJoinedMap = {};


    if (
        tournamentCache.length === 0
    ) {
        return;
    }


    const ids =
        tournamentCache.map(
            tournament =>
                tournament.id
        );


    try {

        const {
            data,
            error
        } =
            await supabaseClient
                .from(
                    "tournament_players"
                )
                .select(
                    "id, tournament_id, player_id"
                )
                .in(
                    "tournament_id",
                    ids
                );


        if (error) {

            console.error(
                "Tournament players error:",
                error
            );

            return;

        }


        (data || []).forEach(
            row => {

                const tournamentId =
                    row.tournament_id;


                if (
                    !tournamentJoinedMap[
                        tournamentId
                    ]
                ) {

                    tournamentJoinedMap[
                        tournamentId
                    ] = [];

                }


                tournamentJoinedMap[
                    tournamentId
                ].push(
                    row.player_id
                );

            }
        );


        console.log(
            "Tournament player data loaded."
        );


    } catch (error) {

        console.error(
            "Tournament players exception:",
            error
        );

    }

}


// ============================================================
// LOAD TOURNAMENT RESULTS
// ============================================================

async function loadTournamentResults() {

    tournamentResultCache = {};


    if (
        tournamentCache.length === 0
    ) {
        return;
    }


    const ids =
        tournamentCache.map(
            tournament =>
                tournament.id
        );


    try {

        const {
            data,
            error
        } =
            await supabaseClient
                .from(
                    "tournament_results"
                )
                .select(
                    `
                    id,
                    tournament_id,
                    position,
                    team_name,
                    score,
                    category,
                    created_at
                    `
                )
                .in(
                    "tournament_id",
                    ids
                )
                .order(
                    "position",
                    {
                        ascending: true
                    }
                );


        if (error) {

            console.error(
                "Tournament results error:",
                error
            );

            return;

        }


        (data || []).forEach(
            row => {

                const tournamentId =
                    row.tournament_id;


                if (
                    !tournamentResultCache[
                        tournamentId
                    ]
                ) {

                    tournamentResultCache[
                        tournamentId
                    ] = [];

                }


                tournamentResultCache[
                    tournamentId
                ].push(
                    row
                );

            }
        );


        console.log(
            "Tournament results loaded."
        );


    } catch (error) {

        console.error(
            "Tournament results exception:",
            error
        );

    }

}


// ============================================================
// TOURNAMENT TAB BUTTONS
// ============================================================

function renderTournamentTabs() {

    console.log(
        "Setting tournament tabs..."
    );


    // ---------------------------------------------------------
    // Find buttons by data-tab
    // ---------------------------------------------------------

    const tabs =
        document.querySelectorAll(
            "[data-tab]"
        );


    console.log(
        "Tournament tab buttons found:",
        tabs.length
    );


    tabs.forEach(
        tab => {

            const tabName =
                tab.dataset.tab;


            // Remove previous active styling
            tab.classList.remove(
                "active"
            );


            // Apply active styling
            if (
                tabName ===
                currentTournamentTab
            ) {

                tab.classList.add(
                    "active"
                );

            }


            // Remove old click handler
            // by replacing the button.

            const newTab =
                tab.cloneNode(true);


            tab.parentNode.replaceChild(
                newTab,
                tab
            );


            newTab.addEventListener(
                "click",
                async function () {

                    console.log(
                        "Tournament tab clicked:",
                        this.dataset.tab
                    );


                    currentTournamentTab =
                        this.dataset.tab;


                    // Refresh tab appearance
                    renderTournamentTabs();


                    // Render corresponding data
                    renderTournamentList();

                }
            );

        }
    );

}


// ============================================================
// RENDER CURRENT TAB
// ============================================================

function renderTournamentList() {

    const list =
        getElement(
            "tournamentList"
        );


    if (!list) {

        console.error(
            "tournamentList not found."
        );

        return;

    }


    console.log(
        "Rendering tab:",
        currentTournamentTab
    );


    // ========================================================
    // CALCULATE STATUS FROM DATES
    // ========================================================

    const tournamentsWithStatus =
        tournamentCache.map(
            tournament => {

                const calculatedStatus =
                    tournamentStatusFromDates(
                        tournament.start_date,
                        tournament.end_date
                    );


                return {
                    ...tournament,
                    calculatedStatus
                };

            }
        );


    // ========================================================
    // FILTER CURRENT TAB
    // ========================================================

    const filtered =
        tournamentsWithStatus.filter(
            tournament => {

                return (
                    tournament.calculatedStatus ===
                    currentTournamentTab
                );

            }
        );


    console.log(
        currentTournamentTab +
        " tournaments:",
        filtered.length
    );


    // ========================================================
    // NO DATA
    // ========================================================

    if (
        filtered.length === 0
    ) {

        list.innerHTML =
            `
            <div class="empty-message">

                <div
                    style="
                        font-size:42px;
                        margin-bottom:10px;
                    "
                >
                    🏆
                </div>

                <strong>
                    No ${escapeHtml(
                        currentTournamentTab
                    )} tournaments
                </strong>

                <br><br>

                There are currently no tournaments
                in this category.

            </div>
            `;

        return;

    }


    // ========================================================
    // SHOW TOURNAMENT CARDS
    // ========================================================

    list.innerHTML =
        filtered
            .map(
                tournament =>
                    renderTournamentCard(
                        tournament
                    )
            )
            .join("");

}


// ============================================================
// TOURNAMENT CARD
// ============================================================

function renderTournamentCard(
    tournament
) {

    const status =
        tournament.calculatedStatus ||
        tournamentStatusFromDates(
            tournament.start_date,
            tournament.end_date
        );


    const joinedPlayers =
        tournamentJoinedMap[
            tournament.id
        ] || [];


    const results =
        tournamentResultCache[
            tournament.id
        ] || [];


    const joined =
        currentUserId &&
        joinedPlayers.includes(
            currentUserId
        );


    let buttons = "";


    // ========================================================
    // UPCOMING
    // ========================================================

    if (
        status === "Upcoming"
    ) {

        if (isPlayer()) {

            buttons +=
                `
                <button
                    type="button"
                    class="tournament-action-button"
                    onclick="joinTournament(${Number(
                        tournament.id
                    )})"
                    ${
                        joined
                        ? "disabled"
                        : ""
                    }
                >
                    ${
                        joined
                        ? "✓ JOINED"
                        : "JOIN TOURNAMENT"
                    }
                </button>
                `;

        }


        if (
            canManageTournaments()
        ) {

            buttons +=
                `
                <button
                    type="button"
                    class="tournament-action-button secondary"
                    onclick="openTournamentForm(${Number(
                        tournament.id
                    )})"
                >
                    ✏️ EDIT
                </button>

                <button
                    type="button"
                    class="tournament-action-button danger"
                    onclick="deleteTournament(${Number(
                        tournament.id
                    )})"
                >
                    🗑 DELETE
                </button>
                `;

        }

    }


    // ========================================================
    // ONGOING
    // ========================================================

    if (
        status === "Ongoing"
    ) {

        if (
            safeUrl(
                tournament.live_link
            )
        ) {

            buttons +=
                `
                <a
                    class="tournament-action-button live-link"
                    href="${escapeHtml(
                        safeUrl(
                            tournament.live_link
                        )
                    )}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    ▶ WATCH LIVE
                </a>
                `;

        }


        if (
            canManageTournaments()
        ) {

            buttons +=
                `
                <button
                    type="button"
                    class="tournament-action-button secondary"
                    onclick="openLiveLinkForm(${Number(
                        tournament.id
                    )})"
                >
                    🔗 LIVE LINK
                </button>

                <button
                    type="button"
                    class="tournament-action-button secondary"
                    onclick="openResultForm(${Number(
                        tournament.id
                    )})"
                >
                    🏆 RESULTS
                </button>

                <button
                    type="button"
                    class="tournament-action-button secondary"
                    onclick="openTournamentForm(${Number(
                        tournament.id
                    )})"
                >
                    ✏️ EDIT
                </button>

                <button
                    type="button"
                    class="tournament-action-button danger"
                    onclick="deleteTournament(${Number(
                        tournament.id
                    )})"
                >
                    🗑 DELETE
                </button>
                `;

        }

    }


    // ========================================================
    // FINISHED
    // ========================================================

    if (
        status === "Finished"
    ) {

        buttons +=
            `
            <button
                type="button"
                class="tournament-action-button secondary"
                onclick="showTournamentDetails(${Number(
                    tournament.id
                )})"
            >
                VIEW DETAILS
            </button>
            `;


        if (
            canManageTournaments()
        ) {

            buttons +=
                `
                <button
                    type="button"
                    class="tournament-action-button secondary"
                    onclick="openResultForm(${Number(
                        tournament.id
                    )})"
                >
                    🏆 RESULTS
                </button>

                <button
                    type="button"
                    class="tournament-action-button secondary"
                    onclick="openTournamentForm(${Number(
                        tournament.id
                    )})"
                >
                    ✏️ EDIT
                </button>

                <button
                    type="button"
                    class="tournament-action-button danger"
                    onclick="deleteTournament(${Number(
                        tournament.id
                    )})"
                >
                    🗑 DELETE
                </button>
                `;

        }

    }


    return `
        <div class="tournament-card">

            <div class="tournament-card-top">

                <span
                    class="status-badge"
                >
                    ${escapeHtml(
                        status
                    )}
                </span>

                <span
                    class="event-type-badge"
                >
                    ${escapeHtml(
                        tournament.event_type ||
                        "Classic"
                    )}
                </span>

            </div>


            <div class="tournament-name">
                🏆 ${
                    escapeHtml(
                        tournament.name ||
                        "Gateball Tournament"
                    )
                }
            </div>


            <div class="tournament-info">

                📍 ${
                    escapeHtml(
                        tournament.venue ||
                        "Venue not specified"
                    )
                }

                <br>

                📅 ${
                    formatDate(
                        tournament.start_date
                    )
                }

                &nbsp;→&nbsp;

                ${
                    formatDate(
                        tournament.end_date
                    )
                }

                ${
                    tournament.country
                    ?
                    `
                    <br>
                    🌏 ${
                        escapeHtml(
                            tournament.country
                        )
                    }
                    `
                    :
                    ""
                }

                ${
                    tournament.organizer_name
                    ?
                    `
                    <br>
                    👤 Organizer:
                    ${
                        escapeHtml(
                            tournament.organizer_name
                        )
                    }
                    `
                    :
                    ""
                }

            </div>


            ${
                tournament.description
                ?
                `
                <div
                    class="tournament-description"
                >
                    ${
                        escapeHtml(
                            tournament.description
                        )
                    }
                </div>
                `
                :
                ""
            }


            ${
                status === "Upcoming"
                ?
                `
                <div
                    class="joined-count"
                >
                    👥 ${
                        joinedPlayers.length
                    }
                    player(s) joined
                </div>
                `
                :
                ""
            }


            ${
                status === "Ongoing"
                ?
                `
                <div
                    class="joined-count"
                >
                    🔴 Tournament is ongoing
                </div>
                `
                :
                ""
            }


            ${
                status === "Finished" &&
                results.length > 0
                ?
                renderResultsPreview(
                    results
                )
                :
                ""
            }


            <div
                class="tournament-actions"
            >
                ${buttons}
            </div>

        </div>
    `;

}


// ============================================================
// RESULTS PREVIEW
// ============================================================

function renderResultsPreview(
    results
) {

    const sorted =
        [...results]
            .sort(
                (a, b) =>
                    Number(a.position) -
                    Number(b.position)
            );


    return `
        <div
            class="results-preview"
        >

            <div
                class="results-title"
            >
                🏆 Results
            </div>

            ${
                sorted
                    .map(
                        result =>
                            `
                            <div
                                class="result-row"
                            >

                                <span>
                                    ${
                                        getPositionLabel(
                                            result.position
                                        )
                                    }
                                </span>

                                <strong>
                                    ${
                                        escapeHtml(
                                            result.team_name ||
                                            ""
                                        )
                                    }
                                </strong>

                                <span>
                                    ${
                                        escapeHtml(
                                            result.score ||
                                            ""
                                        )
                                    }
                                </span>

                            </div>
                            `
                    )
                    .join("")
            }

        </div>
    `;

}


// ============================================================
// TOURNAMENT DETAILS
// ============================================================

function showTournamentDetails(
    tournamentId
) {

    const tournament =
        tournamentCache.find(
            item =>
                Number(item.id) ===
                Number(tournamentId)
        );


    if (!tournament) {

        alert(
            "Tournament information not found."
        );

        return;

    }


    const details =
        getElement(
            "tournamentDetailContent"
        );


    if (!details) {

        alert(
            "Tournament details area is missing from index.html."
        );

        return;

    }


    const results =
        tournamentResultCache[
            tournament.id
        ] || [];


    details.innerHTML =
        `
        <h2>
            🏆 ${
                escapeHtml(
                    tournament.name
                )
            }
        </h2>

        <p>
            <strong>Status:</strong>
            ${
                escapeHtml(
                    tournamentStatusFromDates(
                        tournament.start_date,
                        tournament.end_date
                    )
                )
            }
        </p>

        <p>
            <strong>Event Type:</strong>
            ${
                escapeHtml(
                    tournament.event_type ||
                    ""
                )
            }
        </p>

        <p>
            <strong>Venue:</strong>
            ${
                escapeHtml(
                    tournament.venue ||
                    "Not specified"
                )
            }
        </p>

        <p>
            <strong>Country:</strong>
            ${
                escapeHtml(
                    tournament.country ||
                    "Not specified"
                )
            }
        </p>

        <p>
            <strong>Start Date:</strong>
            ${
                formatDate(
                    tournament.start_date
                )
            }
        </p>

        <p>
            <strong>End Date:</strong>
            ${
                formatDate(
                    tournament.end_date
                )
            }
        </p>

        ${
            tournament.organizer_name
            ?
            `
            <p>
                <strong>Organizer:</strong>
                ${
                    escapeHtml(
                        tournament.organizer_name
                    )
                }
            </p>
            `
            :
            ""
        }

        ${
            tournament.description
            ?
            `
            <p>
                <strong>Description:</strong>
                <br>
                ${
                    escapeHtml(
                        tournament.description
                    )
                }
            </p>
            `
            :
            ""
        }


        <hr>


        <h3>
            🏆 Results
        </h3>


        ${
            results.length > 0
            ?
            renderResultsPreview(
                results
            )
            :
            `
            <p class="empty-message">
                No results have been entered yet.
            </p>
            `
        }


        <br>


        <button
            type="button"
            class="tournament-action-button secondary"
            onclick="hideModal('tournamentDetailModal')"
        >
            CLOSE
        </button>

        `;


    showModal(
        "tournamentDetailModal"
    );

}


// ============================================================
// JOIN TOURNAMENT
// ============================================================

async function joinTournament(
    tournamentId
) {

    if (!currentUserId) {

        alert(
            "Please login first."
        );

        return;

    }


    if (!isPlayer()) {

        alert(
            "Only Player accounts can join tournaments."
        );

        return;

    }


    const tournament =
        tournamentCache.find(
            item =>
                Number(item.id) ===
                Number(tournamentId)
        );


    if (!tournament) {
        return;
    }


    const status =
        tournamentStatusFromDates(
            tournament.start_date,
            tournament.end_date
        );


    if (
        status !== "Upcoming"
    ) {

        alert(
            "Only Upcoming tournaments can be joined."
        );

        return;

    }


    try {

        const {
            error
        } =
            await supabaseClient
                .from(
                    "tournament_players"
                )
                .insert({
                    tournament_id:
                        Number(
                            tournamentId
                        ),

                    player_id:
                        currentUserId
                });


        if (error) {
            throw error;
        }


        alert(
            "You have joined the tournament successfully."
        );


        await loadTournamentPage();

    } catch (error) {

        console.error(
            "Join tournament error:",
            error
        );


        if (
            error.code === "23505"
        ) {

            alert(
                "You have already joined this tournament."
            );

        } else {

            alert(
                "Could not join tournament:\n\n" +
                (
                    error.message ||
                    "Unknown error"
                )
            );

        }

    }

}


// ============================================================
// ADD / EDIT TOURNAMENT
// ============================================================

function openTournamentForm(
    tournamentId = null
) {

    if (
        !canManageTournaments()
    ) {

        alert(
            "Only Admin or Organizer can manage tournaments."
        );

        return;

    }


    const form =
        getElement(
            "tournamentForm"
        );


    if (!form) {

        alert(
            "Tournament form is missing from index.html."
        );

        return;

    }


    form.reset();


    const idInput =
        getElement(
            "tournamentId"
        );


    const title =
        getElement(
            "tournamentFormTitle"
        );


    if (
        tournamentId !== null
    ) {

        const tournament =
            tournamentCache.find(
                item =>
                    Number(item.id) ===
                    Number(tournamentId)
            );


        if (!tournament) {
            return;
        }


        if (idInput) {
            idInput.value =
                tournament.id;
        }


        if (title) {
            title.textContent =
                "Edit Tournament";
        }


        getElement(
            "tournamentName"
        ).value =
            tournament.name || "";


        getElement(
            "tournamentVenue"
        ).value =
            tournament.venue || "";


        getElement(
            "tournamentCountry"
        ).value =
            tournament.country || "";


        getElement(
            "tournamentEventType"
        ).value =
            tournament.event_type ||
            "Classic";


        getElement(
            "tournamentStartDate"
        ).value =
            tournament.start_date || "";


        getElement(
            "tournamentEndDate"
        ).value =
            tournament.end_date || "";


        getElement(
            "tournamentDescription"
        ).value =
            tournament.description || "";

    } else {

        if (idInput) {
            idInput.value = "";
        }


        if (title) {
            title.textContent =
                "Add Tournament";
        }

    }


    showModal(
        "tournamentFormModal"
    );

}


// ============================================================
// SAVE TOURNAMENT
// ============================================================

async function saveTournament(
    event
) {

    event.preventDefault();


    if (
        !canManageTournaments()
    ) {

        alert(
            "Only Admin or Organizer can manage tournaments."
        );

        return;

    }


    const id =
        getElement(
            "tournamentId"
        ).value;


    const name =
        getElement(
            "tournamentName"
        ).value.trim();


    const venue =
        getElement(
            "tournamentVenue"
        ).value.trim();


    const country =
        getElement(
            "tournamentCountry"
        ).value.trim();


    const eventType =
        getElement(
            "tournamentEventType"
        ).value;


    const startDate =
        getElement(
            "tournamentStartDate"
        ).value;


    const endDate =
        getElement(
            "tournamentEndDate"
        ).value;


    const description =
        getElement(
            "tournamentDescription"
        ).value.trim();


    if (!name) {

        alert(
            "Please enter tournament name."
        );

        return;

    }


    if (!startDate || !endDate) {

        alert(
            "Please select tournament dates."
        );

        return;

    }


    if (
        endDate < startDate
    ) {

        alert(
            "End date cannot be before start date."
        );

        return;

    }


    const status =
        tournamentStatusFromDates(
            startDate,
            endDate
        );


    const payload = {

        name,

        venue:
            venue || null,

        country:
            country || null,

        event_type:
            eventType,

        start_date:
            startDate,

        end_date:
            endDate,

        description:
            description || null,

        organizer_id:
            currentUserId,

        organizer_name:
            currentUserProfile?.full_name ||
            null,

        status,

        updated_at:
            new Date().toISOString()

    };


    try {

        if (id) {

            const {
                error
            } =
                await supabaseClient
                    .from(
                        "tournaments"
                    )
                    .update(payload)
                    .eq(
                        "id",
                        id
                    );


            if (error) {
                throw error;
            }


            alert(
                "Tournament updated successfully."
            );

        } else {

            const {
                error
            } =
                await supabaseClient
                    .from(
                        "tournaments"
                    )
                    .insert(payload);


            if (error) {
                throw error;
            }


            alert(
                "Tournament added successfully."
            );

        }


        hideModal(
            "tournamentFormModal"
        );


        await loadTournamentPage();

        await loadDashboard();


    } catch (error) {

        console.error(
            "Save tournament error:",
            error
        );


        alert(
            "Could not save tournament:\n\n" +
            (
                error.message ||
                "Unknown error"
            )
        );

    }

}


// ============================================================
// DELETE TOURNAMENT
// ============================================================

async function deleteTournament(
    tournamentId
) {

    if (
        !canManageTournaments()
    ) {

        alert(
            "Only Admin or Organizer can delete tournaments."
        );

        return;

    }


    const tournament =
        tournamentCache.find(
            item =>
                Number(item.id) ===
                Number(tournamentId)
        );


    if (!tournament) {
        return;
    }


    const confirmed =
        confirm(
            "Delete this tournament?\n\n" +
            tournament.name +
            "\n\nAll joined players and results linked to this tournament will also be deleted."
        );


    if (!confirmed) {
        return;
    }


    try {

        const {
            error
        } =
            await supabaseClient
                .from(
                    "tournaments"
                )
                .delete()
                .eq(
                    "id",
                    tournamentId
                );


        if (error) {
            throw error;
        }


        alert(
            "Tournament deleted successfully."
        );


        await loadTournamentPage();

        await loadDashboard();


    } catch (error) {

        console.error(
            "Delete tournament error:",
            error
        );


        alert(
            "Could not delete tournament:\n\n" +
            (
                error.message ||
                "Unknown error"
            )
        );

    }

}


// ============================================================
// LIVE LINK
// ============================================================

function openLiveLinkForm(
    tournamentId
) {

    if (
        !canManageTournaments()
    ) {

        alert(
            "Only Admin or Organizer can manage live links."
        );

        return;

    }


    const tournament =
        tournamentCache.find(
            item =>
                Number(item.id) ===
                Number(tournamentId)
        );


    if (!tournament) {
        return;
    }


    const idInput =
        getElement(
            "liveLinkTournamentId"
        );


    const linkInput =
        getElement(
            "liveLinkInput"
        );


    if (!idInput || !linkInput) {

        alert(
            "Live link form is missing from index.html."
        );

        return;

    }


    idInput.value =
        tournament.id;


    linkInput.value =
        tournament.live_link || "";


    showModal(
        "liveLinkModal"
    );

}


async function saveLiveLink(
    event
) {

    event.preventDefault();


    if (
        !canManageTournaments()
    ) {

        alert(
            "Only Admin or Organizer can manage live links."
        );

        return;

    }


    const tournamentId =
        getElement(
            "liveLinkTournamentId"
        ).value;


    const link =
        getElement(
            "liveLinkInput"
        ).value.trim();


    if (link) {

        if (!safeUrl(link)) {

            alert(
                "Please enter a valid http:// or https:// URL."
            );

            return;

        }

    }


    try {

        const {
            error
        } =
            await supabaseClient
                .from(
                    "tournaments"
                )
                .update({
                    live_link:
                        link || null,

                    updated_at:
                        new Date().toISOString()
                })
                .eq(
                    "id",
                    tournamentId
                );


        if (error) {
            throw error;
        }


        alert(
            "Live link saved successfully."
        );


        hideModal(
            "liveLinkModal"
        );


        await loadTournamentPage();

        await loadDashboard();


    } catch (error) {

        console.error(
            "Save live link error:",
            error
        );


        alert(
            "Could not save live link:\n\n" +
            (
                error.message ||
                "Unknown error"
            )
        );

    }

}


// ============================================================
// RESULTS FORM
// ============================================================

function buildResultInputs(
    tournamentId
) {

    const container =
        getElement(
            "resultInputs"
        );


    if (!container) {

        console.error(
            "resultInputs not found."
        );

        return;

    }


    const existing =
        tournamentResultCache[
            tournamentId
        ] || [];


    const existingCategory =
        existing.length > 0 &&
        existing[0].category
        ?
        existing[0].category
        :
        "Classic";


    container.innerHTML =
        `

        <div class="form-group">

            <label>
                Category
            </label>

            <select
                id="resultCategory"
            >

                <option
                    value="Classic"
                    ${
                        existingCategory ===
                        "Classic"
                        ? "selected"
                        : ""
                    }
                >
                    Classic
                </option>

                <option
                    value="Triple"
                    ${
                        existingCategory ===
                        "Triple"
                        ? "selected"
                        : ""
                    }
                >
                    Triple
                </option>

                <option
                    value="Double"
                    ${
                        existingCategory ===
                        "Double"
                        ? "selected"
                        : ""
                    }
                >
                    Double
                </option>

            </select>

        </div>


        ${
            [1, 2, 3, 4]
                .map(
                    position => {

                        const old =
                            existing.find(
                                row =>
                                    Number(
                                        row.position
                                    ) ===
                                    position
                            );


                        return `

                        <div
                            class="result-input-row"
                        >

                            <label>
                                ${
                                    getPositionLabel(
                                        position
                                    )
                                }
                            </label>

                            <input
                                type="text"
                                id="resultTeam${position}"
                                placeholder="Team / Player name"
                                value="${
                                    escapeHtml(
                                        old?.team_name ||
                                        ""
                                    )
                                }"
                            >

                            <input
                                type="text"
                                id="resultScore${position}"
                                placeholder="Score"
                                value="${
                                    escapeHtml(
                                        old?.score ||
                                        ""
                                    )
                                }"
                            >

                        </div>

                        `;

                    }
                )
                .join("")
        }

        `;

}


function openResultForm(
    tournamentId
) {

    if (
        !canManageTournaments()
    ) {

        alert(
            "Only Admin or Organizer can manage results."
        );

        return;

    }


    const tournament =
        tournamentCache.find(
            item =>
                Number(item.id) ===
                Number(tournamentId)
        );


    if (!tournament) {
        return;
    }


    const idInput =
        getElement(
            "resultTournamentId"
        );


    const title =
        getElement(
            "resultFormTitle"
        );


    if (idInput) {

        idInput.value =
            tournament.id;

    }


    if (title) {

        title.textContent =
            "Tournament Results — " +
            tournament.name;

    }


    buildResultInputs(
        tournament.id
    );


    showModal(
        "resultModal"
    );

}


async function saveTournamentResults(
    event
) {

    event.preventDefault();


    if (
        !canManageTournaments()
    ) {

        alert(
            "Only Admin or Organizer can manage results."
        );

        return;

    }


    const tournamentId =
        getElement(
            "resultTournamentId"
        ).value;


    const category =
        getElement(
            "resultCategory"
        ).value;


    const rows = [];


    for (
        let position = 1;
        position <= 4;
        position++
    ) {

        const team =
            getElement(
                "resultTeam" +
                position
            ).value.trim();


        const score =
            getElement(
                "resultScore" +
                position
            ).value.trim();


        if (team) {

            rows.push({

                tournament_id:
                    Number(
                        tournamentId
                    ),

                position,

                team_name:
                    team,

                score:
                    score || null,

                category

            });

        }

    }


    if (
        rows.length === 0
    ) {

        alert(
            "Please enter at least one result."
        );

        return;

    }


    try {

        const {
            error:
                deleteError
        } =
            await supabaseClient
                .from(
                    "tournament_results"
                )
                .delete()
                .eq(
                    "tournament_id",
                    tournamentId
                )
                .eq(
                    "category",
                    category
                );


        if (deleteError) {
            throw deleteError;
        }


        const {
            error:
                insertError
        } =
            await supabaseClient
                .from(
                    "tournament_results"
                )
                .insert(
                    rows
                );


        if (insertError) {
            throw insertError;
        }


        alert(
            "Tournament results saved successfully."
        );


        hideModal(
            "resultModal"
        );


        await loadTournamentPage();


    } catch (error) {

        console.error(
            "Save tournament results error:",
            error
        );


        alert(
            "Could not save results:\n\n" +
            (
                error.message ||
                "Unknown error"
            )
        );

    }

}


// ============================================================
// TOURNAMENT BUTTONS
// ============================================================

const addTournamentButton =
    getElement(
        "addTournamentButton"
    );


if (addTournamentButton) {

    addTournamentButton.addEventListener(
        "click",
        function () {

            openTournamentForm();

        }
    );

}


const tournamentRefreshButton =
    getElement(
        "tournamentRefreshButton"
    );


if (tournamentRefreshButton) {

    tournamentRefreshButton.addEventListener(
        "click",
        async function () {

            this.disabled = true;

            this.textContent =
                "Loading...";


            try {

                await loadTournamentPage();

            } finally {

                this.disabled = false;

                this.textContent =
                    "Refresh";

            }

        }
    );

}


// ============================================================
// FORMS
// ============================================================

const tournamentForm =
    getElement(
        "tournamentForm"
    );


if (tournamentForm) {

    tournamentForm.addEventListener(
        "submit",
        saveTournament
    );

}


const liveLinkForm =
    getElement(
        "liveLinkForm"
    );


if (liveLinkForm) {

    liveLinkForm.addEventListener(
        "submit",
        saveLiveLink
    );

}


const resultForm =
    getElement(
        "resultForm"
    );


if (resultForm) {

    resultForm.addEventListener(
        "submit",
        saveTournamentResults
    );

}


// ============================================================
// MODAL OUTSIDE CLICK
// ============================================================

document
    .querySelectorAll(
        ".modal-overlay"
    )
    .forEach(
        modal => {

            modal.addEventListener(
                "click",
                function (event) {

                    if (
                        event.target ===
                        modal
                    ) {

                        modal.style.display =
                            "none";

                    }

                }
            );

        }
    );

// ============================================================
// START APPLICATION
// ============================================================

checkExistingSession();
