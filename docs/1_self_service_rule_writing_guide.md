# Avni Self-Service Rule Writing Guide

This guide is designed to help self-service users write simple rules in Avni. 

We encourage users to go through this guide, understand the concepts, and implement the rules on their own. If you find these concepts overwhelming or need additional support, you can reach out to the support team. But please note that each request will go through a budget approval process before any work begins. We kindly ask you to consider the time frame and the nature of your request before raising it to our support team.

## 1. Auto-Populating a Form Element
One of the most basic and useful rules is auto-populating a form element based on a previously entered value.

### Steps for Auto-Population:
1. **Read the value from a previous form element** using:
   ```javascript
   individual.getObservationValue("CONCEPT_NAME_OR_UUID");
   ```
2. **Assign the retrieved value** to the current form element.

### Example: Auto-Populating a Field
Assume we want to auto-populate the "Current Weight" field with the value entered in the "Previous Weight" field.

```javascript
'use strict';
({params, imports}) => {
  const individual = params.entity;
  const formElement = params.formElement;
  
  // Read the value from the previous form element
  const previousWeight = individual.getObservationValue("Previous Weight");
  
  // Assign the retrieved value to the current form element
  return new imports.rulesConfig.FormElementStatus(formElement.uuid, true, previousWeight, [], []);
};
```

### Explanation:
- **Step 1:** Retrieve the value of "Previous Weight" using `getObservationValue`.
- **Step 2:** Assign the retrieved value to the current form element.
- **Step 3:** Return a `FormElementStatus` object to auto-populate the field.

This ensures that users do not need to re-enter values, reducing errors and improving efficiency.

---

## 2. `getObservationValue` vs `getObservationReadableValue`
Avni provides two key methods for retrieving observation values:

### `getObservationValue(CONCEPT_NAME_OR_UUID)`
- Returns the **raw value** stored in the system.
- This could be a **numeric value, coded concept (UUID), date, or boolean**.
- Example:
  ```javascript
  const weight = individual.getObservationValue("Weight");
  console.log(weight); // Might return 70 (if numeric) or a UUID if it's a coded concept
  ```

### `getObservationReadableValue(CONCEPT_NAME_OR_UUID)`
- Returns the **human-readable version** of the value.
- If the value is a **coded concept (UUID)**, it will return the **display name instead of the UUID**.
- Example:
  ```javascript
  const weightCategory = individual.getObservationReadableValue("Weight Category");
  console.log(weightCategory); // Might return "Overweight" instead of a UUID like "abc123-xyz"
  ```

### When to Use Each:
| Method | Use Case |
|--------|---------|
| `getObservationValue` | When you need the **raw data** for calculations (e.g., BMI calculation, checking numerical conditions). |
| `getObservationReadableValue` | When you need a **user-friendly display value** (e.g., showing a category like "Normal", "Underweight"). |

---

## 3. Auto-Calculating a Form Element
Auto-calculation involves reading values from form elements, applying logic, and setting the calculated result in a new form element.

### Steps for Auto-Calculation:
1. **Retrieve values** from required form elements using:
   ```javascript
   individual.getObservationValue("CONCEPT_NAME_OR_UUID");
   ```
2. **Apply logic or calculations** to process the retrieved values.
3. **Assign the calculated value** to the current form element.

### Example: Calculating BMI
Assume we want to calculate BMI based on height and weight entered in the form.

```javascript
'use strict';
({params, imports}) => {
  const individual = params.entity;
  const formElement = params.formElement;
  
  // Retrieve weight and height
  const weight = individual.getObservationValue("Weight");
  const height = individual.getObservationValue("Height");
  
  // Apply the BMI formula
  let bmi;
  if (weight && height) {
      const heightInMeters = height / 100; // Convert cm to meters
      bmi = weight / (heightInMeters * heightInMeters);
  }
  
  // Assign the calculated BMI value
  return new imports.rulesConfig.FormElementStatus(formElement.uuid, true, bmi, [], []);
};
```

### Explanation:
- **Step 1:** Retrieve `Weight` and `Height` values from previous observations.
- **Step 2:** If both values exist, calculate BMI using `weight / (height * height)`.
- **Step 3:** Assign the computed BMI value to the current form element.

This allows users to automatically compute values without manual input, ensuring data consistency and reducing errors.

---

## 4. Conditional Visibility of Form Elements
Conditional visibility allows you to show or hide form elements based on user input. This improves the user experience by displaying only relevant fields.

### Steps for Conditional Visibility:
1. **Retrieve a value** from a previously entered form element.
2. **Check if the condition is met** (e.g., if a certain answer is selected).
3. **Show or hide the form element** based on the condition.

### Example: Show a Field Based on Gender Selection
Assume we want to show a "Pregnancy Status" field only if the user selects "Female" as gender.

```javascript
'use strict';
({params, imports}) => {
  const individual = params.entity;
  const formElement = params.formElement;
  
  // Retrieve gender
  const gender = individual.getObservationReadableValue("Gender");
  
  // Set visibility condition: Only show if gender is Female
  let visibility = (gender === "Female");
  
  return new imports.rulesConfig.FormElementStatus(formElement.uuid, visibility, null, [], []);
};
```

### Explanation:
- **Step 1:** Retrieve the selected gender using `getObservationReadableValue`.
- **Step 2:** If the gender is "Female", the field remains visible; otherwise, it is hidden.
- **Step 3:** Return a `FormElementStatus` object with the visibility condition.

### Example: Hide a Field if Age is Below 18
```javascript
'use strict';
({params, imports}) => {
  const individual = params.entity;
  const formElement = params.formElement;
  
  // Retrieve age
  const age = individual.getAgeInYears();
  
  // Set visibility condition: Hide if age is below 18
  let visibility = (age >= 18);
  
  return new imports.rulesConfig.FormElementStatus(formElement.uuid, visibility, null, [], []);
};
```

### Explanation:
- **Step 1:** Retrieve the age using `getAgeInYears()`.
- **Step 2:** If the age is 18 or above, the field is visible; otherwise, it is hidden.

This method ensures that users only see relevant fields based on their inputs.

---

## 5. Commonly Used Methods
Instead of manually calculating values like age from date of birth, Avni provides several built-in methods to retrieve and process data efficiently. These methods simplify rule writing by removing the need for manual calculations.

| Method | Purpose |
|--------|---------|
| `getAgeInYears()` | Get the individual's age in **years**. Defaults to today if no date is provided. |
| `getAgeInMonths()` | Get the individual's age in **months**. |
| `getAgeInWeeks()` | Get the individual's age in **weeks**. |
| `getObservationValue("Concept")` | Get the **raw value** (e.g., numbers, UUIDs). |
| `getObservationReadableValue("Concept")` | Get the **human-readable** value (e.g., "Male" instead of a UUID). |
| `getRelative("RelationName")` | Get a **related individual** (e.g., mother, father). |
| `getRelationships()` | Get all **non-voided relationships** of an individual. |
| `findLatestObservationFromEncounters("Concept")` | Get the **most recent observation** from all past encounters. |
| `getAllScheduledVisits()` | Get all **scheduled visits** excluding the current encounter. |

These methods ensure **data consistency, accuracy, and efficiency** while writing rules in Avni.