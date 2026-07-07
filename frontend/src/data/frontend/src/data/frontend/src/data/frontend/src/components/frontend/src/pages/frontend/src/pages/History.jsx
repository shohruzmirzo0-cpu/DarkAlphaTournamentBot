import { useEffect, useState } from "react";
import { currentUser } from "../data/currentUser";

function History() {
  const [matches, setMatches] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/matches")
      .then((res) => res.json())
      .then((data) => setMatches(data));
  }, []);

  return (
    <div style={{ color: "white" }}>
      <h1 style={{ textAlign: "center" }}>📜 Turnir Tarixi</h1>

      <div style={{ background: "#1a1d29", padding: "20px", borderRadius: "15px", marginTop: "20px" }}>
        {matches.map((match) => (
          <div key={match.id} style={{ background: "#252a3d", padding: "15px", borderRadius: "10px", marginBottom: "10px" }}>
            <p>🏆 Tur: {match.round}</p>
            <p>⚽️ @{match.homeUser} vs @{match.awayUser}</p>
            <p>
              Natija:{" "}
              {match.homeGoals === null
                ? "Kutilmoqda"
                : match.homeGoals + " - " + match.awayGoals}
            </p>
            <p>
              Holat:{" "}
              {match.status === "pending"
                ? "⏳ Boshlanmagan"
                : match.status === "waiting"
                ? "⌛ Tasdiq kutilmoqda"
                : match.status === "disputed"
                ? "⚠️ Bahsli (admin ko'rib chiqmoqda)"
                : "✅ Tasdiqlangan"}
            </p>

            {match.status === "waiting" && match.submittedBy !== currentUser.username && (
              <div style={{ marginTop: "10px" }}>
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
                  style={{ padding: "8px 15px", marginRight: "10px", border: "none", borderRadius: "8px", background: "#00c853", color: "white", cursor: "pointer" }}
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
                  style={{ padding: "8px 15px", border: "none", borderRadius: "8px", background: "#d32f2f", color: "white", cursor: "pointer" }}
                >
                  ❌ Shikoyat qilish
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default History;
