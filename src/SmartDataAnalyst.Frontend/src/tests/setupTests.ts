import "@testing-library/jest-dom";
import { vi } from "vitest";

const mockAxios = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  create: vi.fn(() => mockAxios),
  defaults: { headers: {} },
};

vi.mock("axios", () => {
  return {
    default: mockAxios,
    __esModule: true,
  };
});

export { mockAxios };
