import { leagues } from "../data/leagues";
import { clubs1Devizion } from "../data/clubs1Devizion";
import ClubLogo from "../components/ClubLogo";
import { useState, useEffect } from "react";

function Home() {
  const currentUser = JSON.parse(
    localStorage.getItem("currentUser")
  );
  const [leaguePlayers, setLeaguePlayers] = useState({
    "La Liga": 0,
    "Premier League": 0,
  });
  const [joinedLeague, setJoinedLeague] = useState(null);
  const [pendingMatches, setPendingMatches] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState(null);
  const [selectedClub, setSelectedClub] = useState(null);

  const isClubMode = (league) =>
    league?.name?.includes("1-Devizion");

  const registerLeague = async (league) => {
    const response = await fetch("http://127.0.0.1:5000/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: currentUser.username,
        league: league.name,
        club: selectedClub ? selectedClub.name : null,
      }),
    });

    const result = await response.json();

    if (result.success) {
      localStorage.setItem("league", league.name);
      if (selectedClub) {
        localStorage.setItem("club", selectedClub.name);
      }
      setJoinedLeague(league.id);

      alert("Muvaffaqiyatli ro'yxatdan o'tdingiz!");
    } else {
      alert(result.message);
    }
  };

  useEffect(() => {
    const savedLeague = localStorage.getItem("league");

    if (savedLeague) {
      const league = leagues.find(
        (l) => l.name === savedLeague
      );

      if (league) {
        setJoinedLeague(league.id);
      }

      setLeaguePlayers((prev) => ({
        ...prev,
        [savedLeague]: 1,
      }));

      fetch("http://127.0.0.1:5000/users")
        .then((res) => res.json())
        .then((users) => {
          const counts = {};

          users.forEach((user) => {
            counts[user.league] =
              (counts[user.league] || 0) + 1;
          });

          setLeaguePlayers(counts);
        });
    }

    fetch("http://127.0.0.1:5000/matches")
      .then((res) => res.json())
      .then((data) => {
        const waiting = data.filter(
          (match) =>
            match.status === "waiting" &&
            match.awayUser === currentUser.username
        );

        setPendingMatches(waiting);
      });
  }, []);

  const participantsCount = Object.values(leaguePlayers).reduce(
    (sum, count) => sum + count,
    0
  );

  return (
    <div>
      <h1 style={{ color: "white", textAlign: "center", marginBottom: "20px" }}>
        🏆 eFootball Champions League
      </h1>

      <div
        style={{
          background: "linear-gradient(135deg, #0d3b1e, #1f6b3d)",
          borderRadius: "20px",
          padding: "25px",
          textAlign: "center",
          marginBottom: "20px",
        }}
      >
        <h2 style={{ color: "#90EE90" }}>Joriy mavsum</h2>
        <h1 style={{ color: "white", fontSize: "60px", margin: "10px 0" }}>#1</h1>
        <p style={{ color: "white" }}>38 kun bo'ladi</p>
        <span style={{ background: "#00c853", color: "white", padding: "6px 15px", borderRadius: "20px" }}>
          Faol
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "20px" }}>
        <div style={{ background: "#1a1d29", borderRadius: "15px", padding: "15px", textAlign: "center", color: "white" }}>
          <h3>👥 Ishtirokchilar</h3>
          <h2>{participantsCount}</h2>
        </div>

        <div style={{ background: "#1a1d29", borderRadius: "15px", padding: "15px", textAlign: "center", color: "white" }}>
          <h3>🏆 Mavsum</h3>
          <h2>#1</h2>
        </div>
      </div>

      <div style={{ background: "#1a1d29", borderRadius: "20px", padding: "20px", color: "white" }}>
        {pendingMatches.map((match) => (
          <div key={match.id} style={{ background: "#252a3d", borderRadius: "15px", padding: "20px", marginBottom: "20px", color: "white" }}>
            <h2>⚠️ Natijani tasdiqlash</h2>
            <p>@{match.homeUser} natijani yubordi:</p>
            <h3>{match.homeGoals} : {match.awayGoals}</h3>

            <button
              onClick={async () => {
                const response = await fetch("http://127.0.0.1:5000/confirm-result", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ matchId: match.id, username: currentUser.username }),
                });
                const result = await response.json();
                if (result.success) {
                  alert("Natija tasdiqlandi!");
                  window.location.reload();
                }
              }}
              style={{ padding: "10px 20px", background: "#00c853", color: "white", border: "none", borderRadius: "8px", cursor: "pointer" }}
            >
              ✅ Tasdiqlash
            </button>

            <button
              onClick={async () => {
                const response = await fetch("http://127.0.0.1:5000/complain-result", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ matchId: match.id, username: currentUser.username }),
                });
                const result = await response.json();
                if (result.success) {
                  alert("Shikoyat yuborildi!");
                  window.location.reload();
                }
              }}
              style={{ padding: "10px 20px", background: "#d32f2f", color: "white", border: "none", borderRadius: "8px", cursor: "pointer", marginLeft: "10px" }}
            >
              ❌ Shikoyat qilish
            </button>
          </div>
        ))}

        <h2>🏆 Ligalar</h2>

        {leagues.map((league) => (
          <div
            key={league.id}
            onClick={() => {
              if (!joinedLeague) {
                setSelectedLeague(league);
                setSelectedClub(null);
              }
            }}
            style={{
              background: selectedLeague?.id === league.id ? "#00aa55" : "#252a3d",
              padding: "15px",
              borderRadius: "10px",
              marginTop: "10px",
              cursor: joinedLeague ? "not-allowed" : "pointer",
            }}
          >
            <h3>{league.name}</h3>
            <p>👥{leaguePlayers[league.name] || 0} / {league.maxPlayers}</p>

            {selectedLeague?.id === league.id && (
              <>
                {isClubMode(league) && (
                  <div style={{ marginTop: "10px" }}>
                    <p style={{ color: "#90EE90", marginBottom: "8px" }}>⚽ Klubingizni tanlang:</p>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                      {clubs1Devizion.map((club) => (
                        <div
                          key={club.id}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedClub(club);
                          }}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            padding: "8px",
                            borderRadius: "8px",
                            background: selectedClub?.id === club.id ? "#00ff66" : "#1a1d29",
                            color: selectedClub?.id === club.id ? "#111" : "white",
                            cursor: "pointer",
                          }}
                        >
                          <ClubLogo club={club} size={26} />
                          <span style={{ fontSize: "13px" }}>{club.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  disabled={
                    joinedLeague ||
                    leaguePlayers[league.name] >= league.maxPlayers ||
                    (isClubMode(league) && !selectedClub)
                  }
                  onClick={(e) => {
                    e.stopPropagation();
                    registerLeague(selectedLeague);
                  }}
                  style={{ width: "100%", marginTop: "10px", padding: "10px", background: "#00ff66", border: "none", borderRadius: "8px", fontWeight: "bold", cursor: "pointer" }}
                >
                  {leaguePlayers[league.name] >= league.maxPlayers
                    ? "Liga to'lgan"
                    : joinedLeague
                    ? "Ro'yxatdan o'tgan"
                    : isClubMode(league) && !selectedClub
                    ? "Avval klub tanlang"
                    : "Ro'yxatdan o'tish"}
                </button>
              </>
            )}

            {joinedLeague === league.id && (
              <p style={{ color: "#90EE90", marginTop: "10px" }}>✅ Siz ligadan ro'yxatdan o'tgansiz</p>
            )}
          </div>
        ))}

        <h2 style={{ marginTop: "20px" }}>📖 Turnir qoidalari</h2>
        <p>⏱️ O'yin davomiyligi: 8 daqiqa</p>
        <p>💪 O'yinchilar holati: Excellent</p>
        <p>📅 Natija yuborish muddati: 24 soat</p>
        <p>✅ Natija ikki tomon tasdiqlagandan keyin hisoblanadi</p>
      </div>
    </div>
  );
}

export default Home;
