import { ReactNode } from "react";
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View, ViewStyle } from "react-native";

export const colors = {
  bg: "#0E1116",
  card: "#171B22",
  border: "#252B35",
  text: "#F2F4F7",
  muted: "#8A93A3",
  accent: "#3DDC97",
  danger: "#FF6B6B",
  warn: "#FFB547",
};

export function Screen({ children, loading, onRefresh }: { children: ReactNode; loading?: boolean; onRefresh?: () => void }) {
  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.bg }}
      contentContainerStyle={{ padding: 16, gap: 12, paddingBottom: 40 }}
      refreshControl={onRefresh ? <RefreshControl refreshing={!!loading} onRefresh={onRefresh} tintColor={colors.muted} /> : undefined}
    >
      {children}
    </ScrollView>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  return <View style={[s.card, style]}>{children}</View>;
}

export function Row({ left, right, sub }: { left: string; right: ReactNode; sub?: string }) {
  return (
    <View style={s.row}>
      <View style={{ flex: 1 }}>
        <Text style={s.text}>{left}</Text>
        {sub ? <Text style={s.muted}>{sub}</Text> : null}
      </View>
      {typeof right === "string" ? <Text style={s.text}>{right}</Text> : right}
    </View>
  );
}

export function Label({ children }: { children: ReactNode }) {
  return <Text style={s.label}>{children}</Text>;
}

export function Big({ children, color }: { children: ReactNode; color?: string }) {
  return <Text style={[s.big, color ? { color } : null]}>{children}</Text>;
}

export function Muted({ children }: { children: ReactNode }) {
  return <Text style={s.muted}>{children}</Text>;
}

export function Bar({ pct, color }: { pct: number; color: string }) {
  return (
    <View style={s.barTrack}>
      <View style={[s.barFill, { width: `${Math.min(100, Math.max(0, pct))}%`, backgroundColor: color }]} />
    </View>
  );
}

export function LoadState({ loading, error }: { loading: boolean; error: string | null }) {
  if (error) return <Card><Text style={{ color: colors.danger }}>Couldn't load: {error}</Text></Card>;
  if (loading) return <ActivityIndicator color={colors.muted} style={{ marginTop: 24 }} />;
  return null;
}

const s = StyleSheet.create({
  card: { backgroundColor: colors.card, borderColor: colors.border, borderWidth: 1, borderRadius: 16, padding: 16, gap: 10 },
  row: { flexDirection: "row", alignItems: "center", gap: 12 },
  text: { color: colors.text, fontSize: 15 },
  muted: { color: colors.muted, fontSize: 13 },
  label: { color: colors.muted, fontSize: 12, fontWeight: "600", letterSpacing: 0.8, textTransform: "uppercase" },
  big: { color: colors.text, fontSize: 34, fontWeight: "700", fontVariant: ["tabular-nums"] },
  barTrack: { height: 8, borderRadius: 4, backgroundColor: colors.border, overflow: "hidden" },
  barFill: { height: 8, borderRadius: 4 },
});
