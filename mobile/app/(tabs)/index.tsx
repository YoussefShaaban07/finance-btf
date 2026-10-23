import { Alert, Pressable, Text } from "react-native";

import { Big, Card, colors, Label, LoadState, Muted, Row, Screen } from "@/components/ui";
import { api, money } from "@/lib/api";
import { useFetch } from "@/lib/useFetch";

const TYPE_LABEL: Record<string, string> = {
  depository: "Cash", investment: "Investments", credit: "Credit Cards", loan: "Loans", other: "Other",
};

export default function NetWorthScreen() {
  const nw = useFetch(api.netWorth);
  const accounts = useFetch(api.accounts);
  const health = useFetch(api.health);

  const refresh = () => { nw.refresh(); accounts.refresh(); };

  const linkSandbox = async () => {
    try {
      const r = await api.sandboxLink();
      Alert.alert("Linked", r.institution);
      refresh();
    } catch (e) {
      Alert.alert("Couldn't link", String(e));
    }
  };

  return (
    <Screen loading={nw.loading} onRefresh={refresh}>
      {health.data?.demo_mode && (
        <Card style={{ borderColor: colors.warn }}>
          <Text style={{ color: colors.warn }}>Demo mode — showing sample data. Add Plaid keys to the backend to link real (or sandbox) accounts.</Text>
        </Card>
      )}

      <LoadState loading={nw.loading && !nw.data} error={nw.error} />
      {nw.data && (
        <Card>
          <Label>Net worth</Label>
          <Big color={nw.data.net_worth >= 0 ? colors.accent : colors.danger}>{money(nw.data.net_worth)}</Big>
          <Row left="Assets" right={money(nw.data.assets)} />
          <Row left="Liabilities" right={money(-nw.data.liabilities)} />
        </Card>
      )}

      {nw.data && (
        <Card>
          <Label>Breakdown</Label>
          {Object.entries(nw.data.by_type).map(([type, amt]) => (
            <Row key={type} left={TYPE_LABEL[type] ?? type} right={money(type === "credit" || type === "loan" ? -amt : amt)} />
          ))}
        </Card>
      )}

      {accounts.data && (
        <Card>
          <Label>Accounts</Label>
          {accounts.data.map((a) => (
            <Row key={a.id} left={a.name} sub={`${a.institution} · ${a.subtype ?? a.type}`}
                 right={money(a.type === "credit" || a.type === "loan" ? -a.balance : a.balance)} />
          ))}
        </Card>
      )}

      {health.data && !health.data.demo_mode && (
        <Pressable onPress={linkSandbox} style={{ backgroundColor: colors.accent, padding: 14, borderRadius: 12, alignItems: "center" }}>
          <Text style={{ color: colors.bg, fontWeight: "700" }}>+ Link sandbox bank</Text>
        </Pressable>
      )}
      <Muted>Pull down to refresh.</Muted>
    </Screen>
  );
}
