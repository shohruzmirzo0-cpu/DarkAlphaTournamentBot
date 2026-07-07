function ClubLogo({ club, size = 40 }) {
  const style = {
    width: size,
    height: size,
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: "bold",
    fontSize: size * 0.45,
    flexShrink: 0,
  };

  if (club.logo) {
    return (
      <img
        src={club.logo}
        alt={club.name}
        style={{ ...style, objectFit: "cover" }}
      />
    );
  }

  return (
    <div
      style={{
        ...style,
        background: club.color || "#333",
        color: club.color === "#F5F5F5" ? "#111" : "#fff",
        border: "2px solid rgba(255,255,255,0.2)",
      }}
    >
      {club.name.charAt(0).toUpperCase()}
    </div>
  );
}

export default ClubLogo;
