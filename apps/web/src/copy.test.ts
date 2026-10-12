import { describe, expect, it } from "vitest";
import { disclaimers } from "./copy";

describe("copy", () => {
  it("exposes the three mandatory disclaimers", () => {
    expect(disclaimers.generated).toContain("cited source");
    expect(disclaimers.outside).toContain("Outside your material");
    expect(disclaimers.simulated).toContain("simulations");
  });
});
