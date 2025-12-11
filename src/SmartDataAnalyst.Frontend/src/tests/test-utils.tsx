import { render } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AppProvider } from "../context/AppContext";

export function renderWithProviders(ui: React.ReactElement) {
  return render(
    <AppProvider>
      <BrowserRouter>{ui}</BrowserRouter>
    </AppProvider>
  );
}
