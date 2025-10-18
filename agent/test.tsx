import React from "react";

const ExampleComponent = () => {
  const handleClick = () => {
    alert("Submitted!");
  };

  return (
    <div>
      <h2>Sign up form</h2>

      {/* ❌ Static lint issue: <label> not associated with input */}
      <label>Username</label>
      <input type="text" placeholder="Enter username" />

      {/* ❌ Static lint issue: missing alt text on image */}
      <img src="/profile.png" />

      {/* ❌ Static lint issue: clickable div instead of button */}
      <div
        onClick={handleClick}
        style={{ background: "blue", color: "white", padding: 8 }}
      >
        Submit
      </div>

      {/* ❌ Static lint issue: no form element for inputs */}
      <input type="password" placeholder="Password" />

      {/* ⚠️ Visual/Runtime issues: */}
      {/* - Low contrast between text and background */}
      <p style={{ color: "#aaa", backgroundColor: "#fff" }}>
        This is some very low-contrast text that’s hard to read.
      </p>

      {/* - Focus outline removed (bad for keyboard users) */}
      <button
        style={{
          outline: "none",
          border: "none",
          background: "green",
          color: "white",
          padding: 8,
        }}
      >
        Continue
      </button>

      {/* - Modal-like div that traps keyboard focus visually but not logically */}
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: "30%",
          background: "white",
          border: "1px solid black",
          padding: 20,
        }}
      >
        <h3>Pop-up info</h3>
        <p>Press ESC to close — but it doesn’t actually close!</p>
      </div>
    </div>
  );
};

export default ExampleComponent;
