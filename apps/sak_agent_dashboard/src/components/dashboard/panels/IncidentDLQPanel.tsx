"use client";

import React from "react";
import { SelfHealingConsole } from "../../SelfHealingConsole";

export function IncidentDLQPanel() {
  return (
    <section aria-labelledby="dlq-incident-heading" className="w-full">
      <SelfHealingConsole />
    </section>
  );
}

export default IncidentDLQPanel;
