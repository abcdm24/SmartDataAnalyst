import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import DataAnalysisPage from "../pages/DataAnalysisPage";
import { vi } from "vitest";
//import type { Mock } from "vitest";
import type { MockInstance } from "vitest";
import { AppProvider } from "../context/AppContext";
import * as dataApi from "../api/dataApi";
vi.mock("../api/dataApi", async () => {
  return {
    uploadCsv: vi.fn(),
    queryData: vi.fn(),
  };
});

(dataApi.uploadCsv as unknown as MockInstance).mockResolvedValueOnce({
  preview: [{ region: "East", sales: 123 }],
});

vi.mocked(dataApi.queryData).mockResolvedValueOnce({ answer: "AI response" });

describe("AnalysisPage", () => {
  it("renders page heading", () => {
    render(
      <AppProvider>
        <DataAnalysisPage />
      </AppProvider>
    );
    expect(
      screen.getByRole("heading", { name: /Smart Data Analysis/i })
    ).toBeInTheDocument();
  });
  it("uploads a file and calls analyze API", async () => {
    render(
      <AppProvider>
        <DataAnalysisPage />
      </AppProvider>
    );

    const file = new File(["a,b,c"], "sample.csv", { type: "text/csv" });
    const fileInput = screen.getByLabelText(/Upload CSV File/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = screen.getByRole("button", { name: /Upload/i });
    fireEvent.click(uploadButton);
    await waitFor(() => {
      expect(dataApi.uploadCsv).toHaveBeenCalled();
    });

    screen.debug();
    const queryInput = await screen.findByPlaceholderText(
      "e.g., what is the average sales per region?"
    );
    fireEvent.change(queryInput, { target: { value: "test question" } });

    const askButton = screen.getByText("Ask AI");
    await fireEvent.click(askButton);

    await waitFor(() => {
      expect(dataApi.queryData).toHaveBeenCalledTimes(1);
    });
  });
});
