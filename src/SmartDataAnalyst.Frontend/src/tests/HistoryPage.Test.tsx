import { render, screen, waitFor } from "@testing-library/react";
import HistoryPage from "../pages/HistoryPage";
// import axios from "axios";
// import { vi } from "vitest";
// import type { MockedFunction } from "vitest";
import { mockAxios } from "./setupTests";

// vi.mock("axios");

describe("HistoryPage", () => {
  beforeEach(() => {
    mockAxios.get.mockReset();
  });

  it("renders history heading", () => {
    render(<HistoryPage />);
    expect(
      screen.getByRole("button", { name: /Clear All/i })
    ).toBeInTheDocument();
  });

  it("loads history items", async () => {
    const fakeHistory = [
      { id: "1", file_name: "Q1", upload_date: "2025-01-01", query_count: 2 },
      { id: "2", file_name: "Q2", upload_date: "2025-01-02", query_count: 3 },
    ];
    mockAxios.get.mockResolvedValueOnce({ data: fakeHistory });
    // const mockedPost = axios.post as unknown as MockedFunction<
    //   typeof axios.post
    // >;
    // mockedPost.mockResolvedValue({
    //   data: [
    //     { id: 1, question: "Q1", answer: "A1" },
    //     { id: 2, question: "Q2", answer: "A2" },
    //   ],
    // });

    render(<HistoryPage />);

    await waitFor(() => {
      expect(screen.getByText(/Q1/)).toBeInTheDocument();
      expect(screen.getByText(/Q2/)).toBeInTheDocument();
    });
  });
});
