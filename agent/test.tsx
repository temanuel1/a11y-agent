const TestComponent = () => {
  const handleClick = () => {
    console.log("clicked");
  };

  return (
    <div>
      <img src="logo.png" />
      <div onClick={handleClick}>Click me</div>
      <input type="text" />
    </div>
  );
};

export default TestComponent;
