## 8. Creating Dashboards

Creating dashboards is just grouping your report cards neatly:

1. Navigate to **App Designer** > **Offline Dashboards**.
2. Click **NEW OFFLINE DASHBOARD**, provide a meaningful name.
3. Create sections (like "Visits", "Stats", etc.).
4. Add your report cards to each section .

![alt text](image-1.png)

#### Adding Global Filters:
You can also apply filters that affect all cards on the dashboard:

Example:
- A "Gender" filter to see data specifically for "Female" or "Male" subjects:

```javascript
'use strict';
({ params, imports }) => {
  let subjects = params.db.objects('Individual').filtered("voided = false");

  if (params.ruleInput) {
    const genderFilter = params.ruleInput.find(f => f.type === 'Gender');
    if (genderFilter) {
      const selectedGender = genderFilter.filterValue[0].name;
      subjects = subjects.filter(ind => ind.gender.name === selectedGender);
    }
  }

  return subjects;
};
```

### Assigning dashboards to users

Dashboards can be assigned based on roles or user groups:

- In **Admin → User Groups → [Group] → Dashboards**, assign dashboards for users.
- Select one as the primary dashboard to appear prominently on the home screen.