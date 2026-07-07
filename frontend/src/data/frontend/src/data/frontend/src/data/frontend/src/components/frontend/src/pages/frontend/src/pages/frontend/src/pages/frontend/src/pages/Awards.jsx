import { useState, useEffect } from "react";

function Awards() {
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    fetch("https://darkalphatournamentbotbackend.onrender.com/users")
      .then((res) => res.json())
      .then((data) => setTeams(data));
  }, []);

  const goldenBall = [...teams].sort((a, b) => b.wins - a.wins).slice(0, 3);
  const goldenBoot = [...teams].sort((a, b) => b.goals - a.goals).slice(0, 3);

  return (
    <div style={{ color: "white" }}>
      <h1 style={{ color: "gold", textAlign: "center", marginBottom: "20px" }}>
        🥇 Sovrinlar
      </h1>

      <div style={{ background: "#1a1f2e", padding: "20px", borderRadius: "15px", marginBottom: "20px" }}>
        <h2 style={{ color: "gold" }}>🏆 Oltin To'p nomzodlari</h2>

        {goldenBall.length === 0 && <p>Hozircha ma'lumot yo'q</p>}

        {goldenBall.map((player, index) => (
          <div key={player.username} style={{ marginBottom: "15px" }}>
            <p>
              {index === 0 ? "🥇" : index === 1 ? "🥈" : "🥉"}{" "}
              @{player.username} | {player.league} | {player.wins} g'alaba
            </p>
            <progress
              value={Math.max(20, Math.round((player.wins / (goldenBall[0].wins || 1)) * 100))}
              max="100"
              style={{ width: "100%" }}
            />
          </div>
        ))}
      </div>

      <div style={{ background: "#1a1f2e", padding: "20px", borderRadius: "15px" }}>
        <h2 style={{ color: "#7CFC00" }}>👟 Oltin Butsa nomzodlari</h2>

        {goldenBoot.length === 0 && <p>Hozircha ma'lumot yo'q</p>}

        {goldenBoot.map((player, index) => (
          <div key={player.username} style={{ marginBottom: "15px" }}>
            <p>
              {index === 0 ? "🥇" : index === 1 ? "🥈" : "🥉"}{" "}
              @{player.username} | {player.league} | {player.goals} gol
            </p>
            <progress
              value={Math.max(20, Math.round((player.goals / (goldenBoot[0].goals || 1)) * 100))}
              max="100"
              style={{ width: "100%" }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export default Awards;
