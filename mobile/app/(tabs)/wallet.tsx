import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { Bar, Big, Card, colors, Label, LoadState, Row, Screen } from "@/components/ui";
import { api, money, prettyCategory } from "@/lib/api";
import { useFetch } from "@/lib/useFetch";

const RANGES = [7, 30, 90];

export default function WalletScreen() {
  const [days, setDays] = useState(30);
  // refetches automatically when `days` changes
  const spending = useFetch(() => api.spending(days), [days]);
  const txns = useFetch(() => api.transactions(days), [days]);
  const pick = setDays;

  const s = spending.data;
  const maxCat = s ? Math.max(...Object.values(s.by_category), 1) : 1;

  return (
    <Screen loading={spending.loading} onRefresh={() => { spending.refresh(); txns.refresh(); }}>
      <View style={{ flexDirection: "row", gap: 8 }}>
        {RANGES.map((d) => (
          <Pressable key={d} onPress={() => pick(d)}
            style={{ paddingVertical: 8, paddingHorizontal: 14, borderRadius: 20, backgroundColor: d === days ? colors.accent : colors.card }}>
            <Text style={{ color: d === days ? colors.bg : colors.text, fontWeight: "600" }}>{d}d</Text>
          </Pressable>
        ))}
      </View>

      <LoadState loading={spending.loading && !s} error={spending.error} />
      {s && (
        <Card>
          <Label>Spent · last {s.days} days</Label>
          <Big>{money(s.spent)}</Big>
          <Row left="Income" right={<Text style={{ color: colors.accent }}>{money(s.income)}</Text>} />
          <Row left="Net" right={<Text style={{ color: s.net >= 0 ? colors.accent : colors.danger }}>{money(s.net)}</Text>} />
        </Card>
      )}

      {s && (
        <Card>
          <Label>By category</Label>
          {Object.entries(s.by_category).map(([cat, amt]) => (
            <View key={cat} style={{ gap: 6 }}>
              <Row left={prettyCategory(cat)} right={money(amt)} />
              <Bar pct={(amt / maxCat) * 100} color={colors.accent} />
            </View>
          ))}
        </Card>
      )}

      {txns.data && (
        <Card>
          <Label>Transactions</Label>
          {txns.data.slice(0, 50).map((t) => (
            <Row key={t.id} left={t.name} sub={`${t.date} · ${prettyCategory(t.category)}`}
              right={<Text style={{ color: t.amount < 0 ? colors.accent : colors.text }}>{money(-t.amount)}</Text>} />
          ))}
        </Card>
      )}
    </Screen>
  );
}
