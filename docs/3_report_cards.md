## 7. Offline Report Cards and Custom Dashboards
Avni’s offline reporting allows users to access and view key data (e.g. counts of specific types of individuals, enrolments, or visits). These report cards are grouped into custom dashboards which field users can view in the avni mobile app. 

#### What is a Report Card?
A Report Card is a unit that performs specific queries on your data, displaying essential information like counts or lists of subjects. It’s similar to a widget or small report snippet. It looks like a tile with a number (the indicator value) and a label. Tapping a report card reveals the line list of records that contribute to that number.

Report cards can be of 2 types: 
- **Standard Report Cards**:  Built-in cards with pre-defined logic. Avni already knows how to calculate these, so no custom coding is required.
Here are some available standard report cards:
    - Approved
    - Call tasks
    - Comments
    - Due checklist
    - Open subject tasks
    - Overdue visits
    - Pending approval
    - Recent enrolments
    - Recent registrations
    - Recent visits
    - Rejected
    - Scheduled visits
    - Tasks
    - Total

###



**Custom Report Cards**: Cards with user-defined logic. You will write a custom query (in Realm and JavaScript) to determine what the card shows. A custom card’s query function returns a set of Individuals (or other subject records) that meet certain criteria. The app will display the count of these individuals on the card, and tapping the card shows the list of those individuals.

For custom cards, avni expects the query function to return either:

- A list of Individuals (each individual representing a subject or entity)
OR 
- an object with properties primaryValue, secondaryValue, lineListFunction

In this case, 
- primaryValue is the main number to display (as a string). 
- secondaryValue is an optional secondary metric (e.g. a percentage or comparison, as a string in parentheses). 
- lineListFunction is a function that returns the list of Individuals to be listed when the card is clicked. (This function should always return the list of subjects that the card represents​.)

In other words, a custom card can either simply return a list (and the card will show the count of that list), or return a more structured object if you want to display a custom primary/secondary value on the card. If you use the object format, ensure that lineListFunction indeed returns the relevant list of subjects.

Example:
```js
return {
  primaryValue: "50",
  secondaryValue: "(25%)",
  lineListFunction: () => listOfMatchingIndividuals
};
```
This would show 50 (25%) on the card, and the list function would provide the actual 50 records when the card is opened.

### Standard card filters
Some standard report cards support additional filters at the card level, which you can configure in the App Designer when creating the card. The following filters are supported for certain standard card types​:
1. Subject Type - filter to only count subjects of a specific type (e.g. only Individuals, only Households, etc.).
2. Program - filter to only include subjects enrolled in a specific program.
3. Encounter Type - filter to only include encounters of a certain type.
4. Recent Duration (e.g. recent registrations within last N days).
These filters are available for standard card types like overdue visits, scheduled visits, total, and the various other cards​.

For example, you could create a 'Overdue visits' card and restrict it to Subject Type - Beneficiary, Program - Pregnancy, Encounter Type - Delivery. This would then automatically show the count of overdue Delivery visits for Beneficiary subjects in the Pregnancy program - all without writing any custom code (just by selecting those filters in the UI)​

<!-- Note: If you apply the same kind of filter both at the report card level and again at the dashboard level (more on dashboard level filters later), it can lead to confusion. The card level filter is applied first, then the dashboard filter, which might result in a user selecting a filter value that doesn’t actually reflect in the card (because the card was pre-filtered differently)​. It’s best to avoid mixing the same filter type in both places. For instance, do not configure a card to only show Individual subjects and then also give the user a dashboard level Subject Type filter if the user picks 'Household' at the dashboard, the card would still only show Individuals due to its internal filter, which is counter intuitive​ -->


### Creating a Report Card (Step-by-Step)
Creating a new report card in avni is straightforward:
1. Go to **App Designer**.
2. Navigate to the "Report Card" tab in the left menu​.
3. Click on **New offline report card**.
4. Enter a name and optional description for the card. The name will be the title of the card shown to users (so choose something clear like "Adolescent Girls (10-19 yrs)" or "High-Risk Pregnancies").
5. Choose the Type of report card:
    - If it’s a Standard card, select the specific standard category (from the list like Overdue Visits, Total, etc.) 
    - If it’s a Custom card, a code editor will appear for you to write the query logic (covered in the next section).
    
6. (Optional) Pick a Color for the card. Standard cards often have default colors, but you can choose colors to visually distinguish cards on the dashboard (e.g., red for critical indicators, green for positive indicators).
7. Save the report card and your card is ready!

Once saved, the card is available to be added into a dashboard. You can create as many report cards as needed to cover different indicators.


> Tip: When naming report cards, make them self-explanatory. Field users should grasp what the number represents at a glance. For example, instead of a vague name like 'Indicator 1', use 'Women with high risk pregnancy' or 'Households with no toilet' etc., which clearly conveys the metric.


After syncing the mobile app, field users will see the card on their dashboard (once it’s added to a dashboard and assigned to their user group). The card will display a primary number, typically the count of records matching the criteria. If a secondary value is provided (for custom cards), it will show in smaller text (often in parentheses or a smaller font next to or below the primary value). 

When the user taps the card, the app will show the line list of entries that the card represents. For example, if the card is 'Pregnant women' with a count of 5, tapping it might list 5 women who are enroled into pregnancy program. This drill-down helps users identify which records contribute to an indicator, not just the aggregate number.


## Writing Custom Report Card Queries

The power of avni’s custom report cards comes from the ability to write Realm query functions that run on the device’s local database (Realm database). This allows implementers to define virtually any logic for computing an indicator. In this section, we’ll cover how to write these queries, with emphasis on using **Realm queries** for efficiency and using JavaScript for complex logic only when needed.

### The Custom Query Function Environment

When writing a custom report card query, avni provides a function signature like: 

```js
({params, imports}) => {
   // your code here
}
```

- `params.db` - This is the Realm database instance, which you’ll use to query data 

e.g., 
```js
params.db.objects('Individual')
``` 
to get all Individual records.

- `params.ruleInput` - This carries any **dashboard filter inputs** (if the card is on a dashboard with filters applied – more on this later).
- `imports` - This provides useful libraries and utilities that you might need. Common ones include Lodash (`imports.lodash` as `_`) for collection utilities, and Moment.js (`imports.moment`) for date handling. Avni also provides some helper methods on data objects (for example, individuals have methods like `getAgeInYears()` or `getObservationReadableValue(conceptName)` to easily retrieve calculated properties).

Your function should `return` either a list of objects (usually Individuals) or an object with the `primaryValue`, `secondaryValue`, and `lineListFunction` as described earlier.

A very simple example of a custom query (returning a list of all individuals in the system):

```js
'use strict';
({params}) => {
    // Fetch all non-voided individuals
    return params.db.objects('Individual').filtered("voided = false");
};
```

This would create a card showing the total count of all individuals. However, most useful cards will have additional filtering logic.

Let’s explore a few common report card use cases and how to implement them using Realm or JavaScript queries. 

### Example 1: Adolescent Girls Count

**Scenario:** We want a report card showing the number of **adolescent girls (aged 10–19)** enrolled in our system, and a line list of who they are. This could be useful in an adolescent health program or an education context.

**Approach:** We’ll filter individuals by gender and age. Age isn’t a stored field directly, but assuming the Individual’s date of birth (DOB) is recorded, we can calculate age or use the provided helper function `getAgeInYears()`. We will use a combination of a Realm query and a JavaScript filter to achieve this:

```js
'use strict';
({params}) => {
    // Start with all female individuals (to minimize data loaded)
    let girls = params.db.objects('Individual')
               .filtered("voided = false AND gender.name = 'Female'");
    // Now apply age filter in JavaScript
    girls = girls.filter(individual => {
        const age = individual.getAgeInYears();
        return age >= 10 && age <= 19;
    });
    return girls;
};
```

**Explanation:** First, we used `.filtered` on the database (`params.db`) to get only female individuals who are not voided. This filtering happens within Realm (the local database engine), which is efficient. Then we used JavaScript `.filter(...)` on the resulting collection to keep only those with age between 10 and 19. The reason we did the age check in JS is that calculating age might not be directly possible in a Realm query (since it involves the current date). By doing the gender filter in Realm, we reduced the number of records that the JavaScript filter has to sift through. 

If we had not filtered by gender in the database first, and instead pulled *all* individuals into memory and then filtered by gender and age, it would be slower, especially if the database has thousands of records. Always try to push as much filtering as possible into the Realm query.

### Example 2: High-Risk Pregnant Women

**Scenario:** In a maternal health program, certain conditions (like low weight, low hemoglobin, or high number of previous children) might classify a pregnant woman as 'high-risk'. We want a card that shows how many pregnant women are high-risk **currently**, and list them out.

**Approach:** We need to identify *Pregnant Woman* program enrollments and check their latest observations for specific high-risk indicators. This is more complex logic, but avni provides methods like `findLatestObservationInEntireEnrolment(conceptName)` to get the latest value of a particular observation for a program enrolment. We will combine a Realm subquery to find all individuals enrolled in the Pregnancy program with a JS function to evaluate the risk criteria.

```js
'use strict';
({params, imports}) => {
    const _ = imports.lodash;
    // Helper to check if an enrolment has any high-risk flags
    const isHighRiskWoman = (enrolment) => {
        const weight = enrolment.findLatestObservationInEntireEnrolment('Weight');
        const hb = enrolment.findLatestObservationInEntireEnrolment('Hb');
        const liveChildren = enrolment.findLatestObservationInEntireEnrolment('Number of live children');
        return (
            (weight && weight.getReadableValue() < 40) ||    // very low weight
            (hb && hb.getReadableValue() < 8) ||             // very low hemoglobin
            (liveChildren && liveChildren.getReadableValue() > 3)  // more than 3 children
        );
    };

    return {
      lineListFunction: () => 
        // Realm query: find all Individuals with at least one encounter of type "Monthly monitoring of pregnant woman"
        // (to ensure they're actively pregnant and monitored)
        params.db.objects('Individual')
          .filtered(`SUBQUERY(enrolments, $enrolment, 
                      SUBQUERY($enrolment.encounters, $enc, 
                               $enc.encounterType.name = 'Monthly monitoring of pregnant woman' 
                               and $enc.voided = false).@count > 0 
                      and $enrolment.program.name = 'Pregnant Woman' 
                      and $enrolment.voided = false 
                      and voided = false).@count > 0`)
          .filter(individual => 
              individual.voided === false && 
              _.some(individual.enrolments, enrolment => 
                    enrolment.program.name === 'Pregnant Woman' && isHighRiskWoman(enrolment)
              )
          )
    };
};
```

In this example, we return an object with only a `lineListFunction` (and no explicit primaryValue). By default, the card will display the count of individuals returned by `lineListFunction` as the primary value. The code logic does the following:

- Defines `isHighRiskWoman(enrolment)` to check the latest Weight, Hb, and Number of live children observations in a pregnancy enrolment, and flags it if criteria meet our thresholds.
- Uses a Realm `.filtered` query with nested `SUBQUERY` to pre-select Individuals who are:
  - Enrolled in the **Pregnant Woman** program.
  - Have at least one **“Monthly monitoring of pregnant woman”** encounter (and none of those encounters are voided). This is a way to ensure we’re focusing on currently followed pregnancies.
  - (Implicitly, we check `voided = false` on individuals and enrolments to ignore voided records.)
- The Realm query gives us all potentially relevant individuals. We then use a JavaScript `.filter` with Lodash’s `_.some` to find those among the enrolments that satisfy `isHighRiskWoman`.
- The result is the list of high-risk pregnant women.

The card will show the number of such women (for example, '**7**' if there are seven high-risk cases), and tapping it will list their names. This is a powerful example of combining Realm queries for what they're good at (filtering by program and encounter existence) with JavaScript for the complex conditional logic (evaluating observations and numeric thresholds).

### Realm `.filtered` vs JavaScript `.filter`: Best Practices

As seen in the examples above, there are two ways to filter data in avni’s query functions:

- **Using Realm queries (`.filtered`)** - This runs the filtering on the database engine (Realm) itself. It uses a query language syntax (similar to a subset of SQL) and can perform sophisticated filtering, including on nested objects via `SUBQUERY`. Realm queries are **fast** and efficient, especially for large datasets, because they only load the matching records.
- **Using JavaScript filtering (`.filter` with a callback)** - This loads the candidate objects into memory (from the device’s database) and then uses a JavaScript function to test each object for a condition.

**Best Practice:** **Do as much filtering as possible in Realm** and use JavaScript only for what Realm cannot do. The more data you load into memory, the slower the reports will be. If a filter condition can be expressed in the Realm query language, use `.filtered` for it. Use JavaScript filtering only for things like custom calculations or function calls that the Realm query cannot perform (e.g., computing age, calling helper methods like `isHighRiskWoman`, or using complex logic).

To illustrate the difference:

- *Realm Query Example:* Fetch all individuals enrolled in the *Child* program using a Realm subquery:
  ```js
  'use strict';
  ({params}) => ({
      lineListFunction: () => params.db.objects('Individual')
          .filtered("SUBQUERY(enrolments, $e, $e.program.name = 'Child' and $e.voided = false).@count > 0")
  });
  ```
  This query is executed by Realm internally and will directly return only those individuals who have an enrolment in program 'Child'.

- *In-Memory JS Filter Example:* Achieve the same result by retrieving all individuals then filtering in JavaScript:
  ```js
  'use strict';
  ({params}) => {
      return params.db.objects('Individual')
          .filter(ind => ind.voided === false && 
                         _.some(ind.enrolments, e => e.program.name === 'Child'));
  };
  ```
  This approach first loads **all** individuals and then checks each one’s enrolments in JavaScript. If you have thousands of records, that can be significantly slower.

In summary, the first approach (Realm query) is much more performant and is the recommended style. Only fall back to the second approach for parts of the logic that cannot be handled by Realm’s query syntax.

**Additional Tips for Writing Efficient Queries:**
- Use **indexed fields** or keys in your query if possible (e.g., `uuid` or `id` if checking specific identifiers).
- Avoid wild-card or `contains` queries on large text if possible, as they may be slower.
- When filtering by observations or relationships, use `SUBQUERY` in Realm with specific criteria (like concept UUIDs or names) rather than pulling all observations and filtering in JS.
- If you need to combine results from multiple entity types (e.g., count of individuals based on encounters), consider querying the child entity (encounter) and then mapping to individuals. 


## Nested Report Cards (Compound Cards)

In some cases, you may want a single logical report to display **multiple related numbers** as separate cards. Avni supports **Nested Report Cards** to handle these scenarios. A nested report card is essentially one custom query that returns *multiple* card results.

**When to use nested cards?** When you have indicators that are computed with very similar logic or from the same dataset, and you want to avoid duplication and performance overhead. For example, suppose you need to display **Total SAM children** and **Total MAM children** (severely and moderately malnourished children). If you created two separate report cards, both might run almost the same query (just changing the severity criteria), possibly each taking 20–30 seconds. The dashboard would only load after both finish (nearly a minute). By combining them into one nested card query, you can fetch the data once (say, retrieve all malnourished children) and then simply split into two counts, producing results much faster (around 30 seconds instead of 60). It also avoids code duplication. You write one function instead of two.

### How to Create a Nested Report Card

A nested report card is created by writing a **custom report card** that returns an object with a special property `reportCards`. The value of `reportCards` is an array of card definitions. Each entry in this array is an object similar to a custom card’s return format, with its own `cardName`, `primaryValue`, etc. Avni will then render each of those as a separate sub-card (usually displayed together in the UI under a common card group).

**Structure of a nested card return:**

```js
'use strict';
({params, imports}) => {
    // ... perform combined logic ...
    return {
        reportCards: [
            {
                cardName: 'Category A',
                cardColor: '#123456',    // optional custom color
                textColor:  '#FFFFFF',   // optional text color on the card
                primaryValue: '10',
                secondaryValue: '(50%)',
                lineListFunction: () => { /* return list of records for Category A */ }
            },
            {
                cardName: 'Category B',
                // cardColor, textColor as needed
                primaryValue: '10',
                secondaryValue: '(50%)',
                lineListFunction: () => { /* return list of records for Category B */ }
            }
            // ... up to 9 such entries ...
        ]
    };
};
```

Each object in `reportCards` array can have:
- **cardName** – Label for that sub-card (shown to users).
- **cardColor**, **textColor** – (Optional) styling for the card background/text.
- **primaryValue**, **secondaryValue** – Strings for the values to display.
- **lineListFunction** – function returning the list of records corresponding to that sub-card's value.

Avni supports up to **9** sub-cards in one nested card. 

### Example 3: Gender Distribution 
Suppose you want a dashboard card that shows the count of male vs female beneficiaries. Instead of two separate cards, you can create one nested card that yields two sub-cards:

```js
'use strict';
({params}) => {
    // Get all individuals (for simplicity, assume subjectType "Individual")
    const all = params.db.objects('Individual').filtered("voided = false");
    const males = all.filtered("gender.name = 'Male'");
    const females = all.filtered("gender.name = 'Female'");
    return {
      reportCards: [
        {
          cardName: 'Male',
          primaryValue: males.length.toString(),
          secondaryValue: null,
          lineListFunction: () => males
        },
        {
          cardName: 'Female',
          primaryValue: females.length.toString(),
          secondaryValue: null,
          lineListFunction: () => females
        }
      ]
    };
};
```

This single report card will show two tiles: 'Male' and 'Female', each with the respective count. Each tile can be clicked to see the list of male or female individuals. All the heavy lifting (fetching all individuals) is done once at the top; the rest is just splitting into two lists, which is efficient.

**Note:** When configuring a nested report card in the App Designer, make sure the number of sub-cards you intend to return matches what your code returns. If there’s a mismatch (say your code returns 2 `reportCards` objects but you configured placeholders for 3, or vice versa), the app will show an error for that card. 

Nested report cards are not a separate type in the UI. You create a custom card and write the function in this format. In the mobile app, the nested cards might appear as a group of colored tiles together. They might also share a section title or be under one dashboard section (depending on configuration). Each sub--ard behaves like a normal card for tapping and listing details.

## More examples...

### **Example 34: Individuals Currently Enrolled in the Pregnancy Program**

```javascript
'use strict';
({ params, imports }) => {
  return params.db.objects('Individual').filtered(`
    voided = false AND
    SUBQUERY(enrolments, $e,
      $e.program.name == 'Pregnancy' AND
      $e.programExitDateTime == null
    ).@count > 0
  `);
};
```
This function retrieves all non-voided individuals from the database and checks if they are currently enrolled in the `Pregnancy` program. It uses a `SUBQUERY` to filter out individuals whose enrolment exists and has no exit date (`programExitDateTime == null`), indicating an active enrollment.

### **Example 5: Individuals Who Have Exited the Pregnancy Program**

Understanding how many individuals have completed or exited a program is important for follow-up care and outcome analysis.

```javascript
'use strict';
({ params, imports }) => {
  return params.db.objects('Individual').filtered(`
    voided = false AND
    SUBQUERY(enrolments, $e,
      $e.program.name == 'Pregnancy' AND
      $e.programExitDateTime != null
    ).@count > 0
  `);
};
```

This function filters for individuals who were enrolled in the `Pregnancy` program and have a **non-null exit date**, meaning they have exited the program.


### **Example 6: Individuals in the Pregnancy Program with ANC Visits**

```javascript
'use strict';
({ params, imports }) => {
  return params.db.objects('Individual').filtered(`
    voided = false AND
    SUBQUERY(enrolments, $e,
      $e.program.name == 'Pregnancy' AND
      $e.programExitDateTime == null AND
      SUBQUERY($e.encounters, $enc,
        $enc.encounterType.name == 'ANC'
      ).@count > 0
    ).@count > 0
  `);
};
```

This function targets individuals actively enrolled in the `Pregnancy` program and checks if they've had **at least one ANC (Antenatal Care)** encounter. Realm `SUBQUERY` filters both enrolments and their associated encounters.

### **Example 7: High-Risk Pregnancies Based on ANC Observations**

```javascript
'use strict';
({ params, imports }) => {
  const HIGH_RISK_UUID = '80b7a6ab-6cc4-44e7-85c6-7e2859c0f72a';
  const NONE_UUID = '521f40f7-2b52-4af1-9fbe-94740e6cd3ee';

  return params.db.objects('Individual').filtered(`
    voided = false AND
    SUBQUERY(enrolments, $e,
      $e.program.name == 'Pregnancy' AND
      $e.programExitDateTime == null AND
      SUBQUERY($e.encounters, $enc,
        $enc.encounterType.name == 'ANC' AND
        SUBQUERY($enc.observations, $obs,
          $obs.concept.uuid == '${HIGH_RISK_UUID}' AND
          NOT $obs.valueJSON CONTAINS '${NONE_UUID}'
        ).@count > 0
      ).@count > 0
    ).@count > 0
  `);
};
```

This function identifies currently enrolled pregnant individuals who have been flagged **high-risk** during ANC visits. It uses nested Realm `SUBQUERY` filters to find ANC encounters with a specific concept UUID, excluding any observation marked as "None".


### **Example 8: Nested Report Cards for Pregnancy Program Overview**

In this case, we group individuals under a broader "Pregnancy Program" card, subdivided into currently enrolled and exited groups.

```javascript
'use strict';
({ params, imports }) => {
  const individuals = params.db.objects('Individual').filtered("voided = false");

  const enrolled = individuals.filtered(`
    SUBQUERY(enrolments, $e,
      $e.program.name == 'Pregnancy' AND
      $e.programExitDateTime == null
    ).@count > 0
  `);

  const exited = individuals.filtered(`
    SUBQUERY(enrolments, $e,
      $e.program.name == 'Pregnancy' AND
      $e.programExitDateTime != null
    ).@count > 0
  `);

  return {
    reportCards: [
      {
        cardName: 'Pregnancy Program',
        nestedCards: [
          {
            cardName: 'Currently Enrolled',
            primaryValue: enrolled.length.toString(),
            lineListFunction: () => enrolled
          },
          {
            cardName: 'Exited',
            primaryValue: exited.length.toString(),
            lineListFunction: () => exited
          }
        ]
      }
    ]
  };
};
```

### Example 9:

```javascript
'use strict';
({ params, imports }) => {
  let allIndividuals = params.db.objects('Individual').filtered("voided = false");

  let adults = allIndividuals.filter(ind => ind.age >= 18);
  let children = allIndividuals.filter(ind => ind.age < 18);

  return {
    reportCards: [
      { cardName: "Adults", primaryValue: adults.length, lineListFunction: () => adults },
      { cardName: "Children", primaryValue: children.length, lineListFunction: () => children }
    ]
  };
};
```
