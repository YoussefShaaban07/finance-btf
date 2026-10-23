import { Text } from "react-native";

import { Bar, Big, Card, colors, Label, LoadState, Muted, Row, Screen } from "@/components/ui";
import { api, money } from "@/lib/api";
import { useFetch } from "@/lib/useFetch";

// Under 30% is the common rule of thumb for credit score health; under 10% is ideal.
const utilColor = (pct: number) => (pct < 10 ? colors.accent : pct < 30 ? colors.warn : colors.danger);

const daysUntil = (iso: string) => Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000);

export default function CardsScreen() {
  const { data, error, loading, refresh } = useFetch(api.creditCards);

  const totalBal = data?.reduce((s, c) => s + c.balance, 0) ?? 0;
  const totalLimit = data?.reduce((s, c) => s + (c.limit ?? 0), 0) ?? 0;
  const overall = totalLimit ? (totalBal / totalLimit) * 100 : 0;

  return (
    <Screen loading={loading} onRefresh={refresh}>
      <LoadState loading={loading && !data} error={error} />
      {data && (
        <Card>
          <Label>Total card balance</Label>
          <Big>{money(totalBal)}</Big>
          <Row left="Overall utilization" right={<Text style={{ color: utilColor(overall), fontWeight: "700" }}>{overall.toFixed(1)}%</Text>} />
          <Bar pct={overall} color={utilColor(overall)} />
          <Muted>Keep it under 30% (ideally under 10%) to help your credit score.</Muted>
        </Card>
      )}

      {data?.map((c) => {
        const pct = c.utilization_pct ?? 0;
        const due = c.next_due_date ? daysUntil(c.next_due_date) : null;
        return (
          <Card key={c.account_id}>
            <Row left={c.name} right={money(c.balance)} sub={c.limit ? `of ${money(c.limit)} limit` : undefined} />
            <Bar pct={pct} color={utilColor(pct)} />
            <Row left="Utilization" right={`${pct.toFixed(1)}%`} />
            {c.apr != null && <Row left="APR" right={`${c.apr.toFixed(2)}%`} />}
            {c.minimum_payment != null && <Row left="Minimum payment" right={money(c.minimum_payment)} />}
            {due != null && (
              <Row left="Due" right={<Text style={{ color: due <= 5 ? colors.danger : colors.text }}>{due <= 0 ? "Today" : `in ${due} days`}</Text>} />
            )}
          </Card>
        );
      })}
    </Screen>
  );
}
