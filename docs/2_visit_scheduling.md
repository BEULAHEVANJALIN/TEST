## 6. Visit Scheduling
Avni’s **visit scheduling** feature allows you to automatically create follow-up visits (encounters) based on rules. 

A _Visit Schedule Rule_ is a JavaScript rule you attach to a form (in the App Designer under the **Rules** tab) to schedule future visits when certain events occur (e.g., after a form is submitted). This rule is triggered when the user completes the form (before the final confirmation screen). The rule function receives a `params` object containing the current context (such as the current encounter or program enrolment), and it should **return an array of visit schedule objects** representing the visits to be scheduled. 

<!-- (https://avni.readme.io/docs/rules-concept-guide) -->

### Step 1: Identify the Trigger and Context  
First, decide **when and where** you want to schedule the visit. In Avni, visit schedules are typically created at the end of a form submission. For example, you might schedule a follow-up visit when a patient is enroled in a program or after any form is filled. 

The context (`params.entity`) could be:  
- A **ProgramEnrolment** (if the rule is attached to an enrolment form),  
- A **ProgramEncounter** (if attached to a program encounter form, i.e., a visit within a program), or  
- A general **Encounter** or **Subject** (for rules on general forms or registration).  

Knowing the context is important because you will use it to calculate dates and conditions. For instance, if scheduling after a program enrolment, you might base the next visit on the enrolment date; if after an encounter, you use the encounter’s date.

### Step 2: Initialize the VisitScheduleBuilder  
Avni provides a helper class `VisitScheduleBuilder` to simplify building visit schedules. Start by creating an instance of this builder, passing in the context. This builder will accumulate all the visits you want to schedule. For example: 

```js
({ params, imports }) => {
  // Get the current context (e.g., program enrolment or encounter)
  const programEnrolment = params.entity;  
  // Initialize the VisitScheduleBuilder with the context.
  const scheduleBuilder = new imports.rulesConfig.VisitScheduleBuilder({ 
    programEnrolment // using programEnrolment context in this example
  });
  …
}
``` 

In the above snippet, we use `params.entity` as the context and pass it into the builder. If your rule is on an encounter form, you might do `const programEncounter = params.entity;` and then `new VisitScheduleBuilder({ programEncounter })` instead (similarly for a general encounter, use `{ encounter: params.entity }`). 

The builder doesn’t schedule anything on its own until we add visits in the next step.

### Step 3: Define the Visit(s) to Schedule with `.add()`  
Use the builder’s `.add()` method to specify each visit you want to schedule. The `.add()` method takes a **visit schedule object** with details about the future visit. At minimum, you should provide:  
- **`name`** – A short name or label for the visit (what the user will see, e.g., `"Follow-up Visit"`).  
- **`encounterType`** – The type of the encounter to be conducted (it should match an existing encounter type in your app).  
- **`earliestDate`** – The earliest date when the visit should be done (due date start).  
- **`maxDate`** – The latest date by which the visit should be done (after this it’s considered overdue).  

These fields are required in each [visit schedule object](https://avni.readme.io/docs/writing-rules#visit-schedule-object). Here’s an example of adding a single visit schedule:

```js
  // Step 3: Add a visit schedule for a follow-up
  scheduleBuilder.add({
    name: "First Follow-up Visit",               // Visit name 
    encounterType: "Postnatal Checkup",          // The form/encounter type for the visit
    earliestDate: programEnrolment.enrolmentDateTime,  // Earliest due date (here, the enrolment date)
    maxDate: programEnrolment.enrolmentDateTime        // Latest due date (same day in this case)
  });
``` 

In this example, we schedule a **“First Follow-up Visit”** of type **“Postnatal Checkup”**, due on the enrolment date itself (both earliest and max on the same date, meaning it’s expected immediately). In practice, you’ll often calculate `earliestDate` and `maxDate` relative to some baseline (like enrolment or encounter date) using a date library. Avni’s rules environment provides **Moment.js** via `imports.moment` for date calculations. For example, to set a visit due 7 days after today, you could do: `earliestDate: imports.moment().add(7, 'days').toDate()` and similarly adjust `maxDate`. **Ensure you convert moment objects to JavaScript Date by calling `.toDate()`**, since Avni expects a Date object (common mistake: forgetting to convert, which can lead to invalid dates).

### Step 4: (Optional) Add Conditions for Scheduling  
Often, you only want to schedule a visit if certain conditions are met. For example, you might only schedule a **“First Follow-up Visit”** if it hasn’t been scheduled before, or schedule a special visit only if a patient is high risk. The `VisitScheduleBuilder.add()` method returns a **condition builder** that lets you chain conditions with methods like `.whenItem(...).equals(...)`, `.greaterThan(...)`, etc.

For instance, to ensure the follow-up is only scheduled once (the first time the rule runs for that program enrolment), you can check that there are no previous encounters of that type:

```js
  // Only schedule if no follow-up has been done yet (e.g., first time)
  scheduleBuilder.add({ ... })
    .whenItem(programEnrolment.getEncounters(true).length)
    .equals(0);
```

In this snippet, `.whenItem(...)` takes an expression or value to evaluate. Here we use `programEnrolment.getEncounters(true).length` which gives the count of encounters in this enrolment – and then `.equals(0)` ensures the condition is only true when that count is 0 (i.e., no encounters yet). The visit will only be included if the condition is met. You can build more complex conditions (multiple `.whenItem()` checks can be chained, or use logical functions provided by the rules engine). If you don’t need any condition (i.e., the visit should always be scheduled), you can omit this and just call `scheduleBuilder.add({...})` without chaining a condition.

### Step 5: Return the Scheduled Visits  
After adding all desired visits (and their conditions), the final step is to return the schedules from your rule function. Typically you will use: 

```js
  // Step 5: Return all the visits that meet their conditions
  return scheduleBuilder.getAll();
};
``` 

Avni will then process this array and create or update the scheduled visits accordingly.

### Additional Examples

Let’s explore a few common scheduling scenarios and how to implement them using `VisitScheduleBuilder`. Each example includes code snippets with comments:

### Example 1: Weekly Checkups (Recurring Weekly Visits)  
**Scenario:** After an initial consultation, schedule a weekly check-up for the next 4 weeks. Each check-up should occur roughly every 7 days after the previous visit. 

```js
({ params, imports }) => {
  const initialEncounter = params.entity;  
  const scheduleBuilder = new imports.rulesConfig.VisitScheduleBuilder({ 
    programEncounter: initialEncounter 
  });
  const baseDate = initialEncounter.encounterDateTime;  // date of the initial consultation

  // Schedule 4 weekly follow-up visits
  for (let week = 1; week <= 4; week++) {
    const dueDate = imports.moment(baseDate).add(7 * week, 'days');  // baseDate + 7, 14, 21, 28 days
    scheduleBuilder.add({
      name: `Week ${week} Follow-up`,         // e.g., "Week 1 Follow-up"
      encounterType: "Weekly Checkup",        // the encounter type for weekly check-ups
      earliestDate: dueDate.toDate(),        // due date for this week
      maxDate: dueDate.add(3, 'days').toDate() // allow a 3-day window after due date
    });
    // (No additional condition; we want all 4 visits scheduled unconditionally)
  }

  return scheduleBuilder.getAll();
};
``` 

**Explanation:** In this code, we loop 4 times to create 4 visit schedules. We use `imports.moment` to calculate the dates: each follow-up is 7 days apart. For example, if the initial encounter was on 01-Jan-2025, then: Week 1 Follow-up due on 08-Jan, Week 2 on 15-Jan, etc. We give each a `maxDate` a few days after the exact due date to accommodate slight delays. All visits are added without any special condition, so they will all be scheduled.

### Example 2: Annual Screening (Yearly Recurrence)  
**Scenario:** After completing an annual health screening, schedule the next one for one year later. For instance, once a patient’s 2025 screening is done, schedule the 2026 screening.

```js
({ params, imports }) => {
  const screeningEncounter = params.entity;  
  const scheduleBuilder = new imports.rulesConfig.VisitScheduleBuilder({ encounter: screeningEncounter });
  
  // Calculate one year from the current screening date
  const nextYearDate = imports.moment(screeningEncounter.encounterDateTime).add(1, 'year');
  scheduleBuilder.add({
    name: "Annual Screening",
    encounterType: "Health Screening",
    earliestDate: nextYearDate.toDate(),           // exactly one year later
    maxDate: nextYearDate.add(1, 'month').toDate()  // give a one-month window to complete
  })
  .whenItem(true).equals(true);  // (optional: always true condition, effectively no condition)

  return scheduleBuilder.getAll();
};
``` 

**Explanation:** We schedule an “Annual Screening” one year after the current one. The `earliestDate` is one year from the encounter’s date, and `maxDate` is one year plus one month (meaning if it’s not done within a month after the anniversary, it becomes overdue). We included a trivial condition `.whenItem(true).equals(true)` just to illustrate that you can use conditions; effectively this schedules the visit unconditionally. In a real scenario, you might not need any condition here (or you might check something like `.whenItem(screeningEncounter.encounterType).equals("Health Screening")` just as a sanity check, but since the rule would likely only run on that form, it’s implicit).

### Example 3: Custom Recurrence Pattern (Conditional Scheduling)  
**Scenario:** In a postnatal care program, you want to schedule more frequent visits for high-risk patients and fewer visits for low-risk patients. For a high-risk mother, schedule visits at 1 week, 2 weeks, and 1 month postpartum. For a normal-risk mother, schedule only a 1-month postpartum visit.

```js
({ params, imports }) => {
  const postnatalEncounter = params.entity;  
  const scheduleBuilder = new imports.rulesConfig.VisitScheduleBuilder({ programEncounter: postnatalEncounter });

  // Determine risk level from an observation in the form (e.g., a field "Risk Level")
  const riskLevel = postnatalEncounter.getObservationValue('Risk Level'); 

  if (riskLevel === 'High') {
    // High-risk: Schedule two weekly visits and one monthly visit
    const base = postnatalEncounter.encounterDateTime;
    // 1 week postpartum
    scheduleBuilder.add({
      name: "Postnatal Checkup - 1 Week",
      encounterType: "Postnatal Checkup",
      earliestDate: imports.moment(base).add(7, 'days').toDate(),
      maxDate: imports.moment(base).add(10, 'days').toDate() // 3-day grace
    });
    // 2 weeks postpartum
    scheduleBuilder.add({
      name: "Postnatal Checkup - 2 Weeks",
      encounterType: "Postnatal Checkup",
      earliestDate: imports.moment(base).add(14, 'days').toDate(),
      maxDate: imports.moment(base).add(17, 'days').toDate()
    });
    // 1 month postpartum
    scheduleBuilder.add({
      name: "Postnatal Checkup - 1 Month",
      encounterType: "Postnatal Checkup",
      earliestDate: imports.moment(base).add(1, 'month').toDate(),
      maxDate: imports.moment(base).add(5, 'weeks').toDate()
    });
  } else {
    // Normal risk: Schedule only the 1-month postnatal checkup
    scheduleBuilder.add({
      name: "Postnatal Checkup - 1 Month",
      encounterType: "Postnatal Checkup",
      earliestDate: imports.moment(postnatalEncounter.encounterDateTime).add(1, 'month').toDate(),
      maxDate: imports.moment(postnatalEncounter.encounterDateTime).add(5, 'weeks').toDate()
    });
  }

  return scheduleBuilder.getAll();
};
``` 

**Explanation:** Here we use an `if` condition in plain JavaScript (outside of the builder’s conditions) to decide how many visits to schedule based on a field `Risk Level`. For high-risk cases, we schedule three follow-ups (at 7 days, 14 days, and 1 month). For others, just one follow-up at 1 month. All these visits use the same `encounterType` (“Postnatal Checkup”) but have different due dates.