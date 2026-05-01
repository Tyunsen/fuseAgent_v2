# Contract: Time Trace Display

## Scope

Defines the required output contract for time-trace QA answers.

## Contract

1. Time mode MUST render one primary gantt graph as its main visualization.
2. The gantt task labels MUST display event names or event phrases, not internal numbered conclusion labels.
3. When evidence includes multiple distinct dates or date ranges, the gantt MUST place them on different time positions rather than collapsing them to one day.
4. If evidence is only month-level, the gantt MAY stay month-level, but it MUST NOT invent day-level precision.
5. Time mode MUST NOT show an extra secondary grouped card, summary card, or duplicate graph card below the main gantt.
6. Raw Mermaid syntax such as `graph TD` MUST NOT remain visible in the rendered answer body.
