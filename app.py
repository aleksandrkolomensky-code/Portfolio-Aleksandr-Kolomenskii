import pandas as pd

changelogs = pd.read_csv('changelogs.csv')
changelogs['changed_at'] = pd.to_datetime(changelogs['changed_at'])
max_date = changelogs['changed_at'].max()
dora_start = max_date - pd.Timedelta(days=90)

print("Max date:", max_date)
print("Dora start:", dora_start)

# Filter
df_90 = changelogs[changelogs['changed_at'] >= dora_start]
print("Total rows in last 90 days:", len(df_90))

# Deployments
df_deploys = df_90[df_90['to_status'] == 'Done'].copy()
df_deploys['date'] = df_deploys['changed_at'].dt.date
print("Unique deployment days in last 90 days (all squads):", df_deploys['date'].nunique())

# Let's see per squad
issues = pd.read_csv('issues.csv')
users = pd.read_csv('users.csv')
df_merged = changelogs.merge(issues, on='issue_id', how='left').merge(users, left_on='assignee_id', right_on='user_id', how='left')

df_merged_90 = df_merged[df_merged['changed_at'] >= dora_start]

for squad in ['Squad Alpha', 'Squad Beta', 'Squad Gamma', 'Squad Delta']:
    df_squad = df_merged_90[df_merged_90['squad'] == squad]
    deploys = df_squad[df_squad['to_status'] == 'Done'].copy()
    deploys['date'] = deploys['changed_at'].dt.date
    print(f"{squad} - Unique deployment days:", deploys['date'].nunique())
