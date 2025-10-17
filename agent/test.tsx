const TestComponent = () => {
  return (
    <div>
      <img src="logo.png" alt="Company logo" />
      <button onClick={() => alert("hi")}>Click</button>
      <input type="text" aria-label="Text input" />
    </div>
  );
};
export default TestComponent;