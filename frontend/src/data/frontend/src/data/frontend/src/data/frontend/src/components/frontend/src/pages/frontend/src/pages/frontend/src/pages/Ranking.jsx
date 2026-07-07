import { useState, useEffect } from "react";

function Ranking() {
  const [search, setSearch] = useState("");
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    fetch("https://darkalphatournamentbotbackend.onrender.com/users")
      .then((res) => res.json())
      .then((data) => setTeams(data));
  }, []);

  const sortedTeams = [...teams].sort((a, b) => b.points - a.points);

  const filteredTeams = sortedTeams.filter((team) =>
    team.username.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <h1 style={{ color: "white", textAlign: "center", marginBottom: "20px" }}>
        🏆 Reyting
      </h1>

      <input
        type="text"
        placeholder="🔍 Ishtirokchini qidiring..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ width: "100%", padding: "12px", borderRadius: "10px", marginBottom: "20px", border: "none", fontSize: "16px" }}
      />

      <table style={{ width: "100%", borderCollapse: "collapse", color: "white", background: "#1a1d29", borderRadius: "15px", overflow: "hidden" }}>
        <thead>
          <tr style={{ background: "#252a3d" }}>
            <th>#</th>
            <th>Ishtirokchi</th>
            <th>O</th>
            <th>G</th>
            <th>D</th>
            <th>M</th>
            <th>GF</th>
            <th>Ochko</th>
          </tr>
        </thead>

        <tbody>
          {filteredTeams.map((team, index) => (
            <tr key={team.username} style={{ textAlign: "center" }}>
              <td>{index + 1}</td>
              <td>@{team.username}</td>
              <td>{team.wins + team.draws + team.losses}</td>
              <td>{team.wins}</td>
              <td>{team.draws}</td>
              <td>{team.losses}</td>
              <td>{team.goals}</td>
              <td style={{ color: "#ffd700", fontWeight: "bold" }}>{team.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Ranking;
