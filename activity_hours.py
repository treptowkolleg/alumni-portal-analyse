import pandas as pd
import plotly.express as px

df = pd.read_csv("url_tracking.csv", sep=";")

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

# Prüfen, ob Konvertierung funktioniert hat
if df["timestamp"].isnull().any():
    print("⚠️ Achtung: Einige Zeitstempel konnten nicht konvertiert werden.")

# Jetzt funktioniert der Zugriff auf .dt
df["hour"] = df["timestamp"].dt.floor("h")

# Gruppieren und visualisieren
activity = df.groupby("hour").size().reset_index(name="count")

# Plot erstellen
fig = px.line(activity, x="hour", y="count", title="Aktivität im Zeitverlauf", markers=True)
fig.update_layout(
    xaxis_title="Zeit",
    yaxis_title="Zugriffe",
    xaxis=dict(tickmode="linear", dtick=1),
    yaxis=dict(tickmode='linear', dtick=1),
)
fig.show()