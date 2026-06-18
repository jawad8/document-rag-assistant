import { render, screen } from "@testing-library/react";

import App from "./App";

test("renders the sign-in experience", () => {
  localStorage.removeItem("token");
  render(<App />);

  expect(
    screen.getByRole("heading", { name: "Document RAG Assistant" })
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
});
