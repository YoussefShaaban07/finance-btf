import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";

import { Big, Card, colors, Label, LoadState, Muted, Row, Screen } from "@/components/ui";
import { api, money, Quote } from "@/lib/api";
import { useFetch } from "@/lib/useFetch";

const DEFAULT_WATCHLIST = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA"];

function Change({ q }: { q: Quote }) {
  const up = q.change >= 0;
  return (
    <Text style={{ color: up ? colors.accent : colors.danger, fontVariant: ["tabular-nums"] }}>
      {money(q.price)}  {up ? "▲" : "▼"} {Math.abs(q.change_pct).toFixed(2)}%
    </Text>
  );
}

export default function StocksScreen() {
  const holdings = useFetch(api.holdings);
  const [watchlist, setWatchlist] = useState(DEFAULT_WATCHLIST); // TODO: persist per user in the backend
  const [input, setInput] = useState("");
  const quoteFetch = useFetch(() => api.quotes(watchlist), [watchlist]);
  const quotes = quoteFetch.data;
  const loadQuotes = quoteFetch.refresh;

  const add = () => {
    const sym = input.trim().toUpperCase();
    if (!sym || watchlist.includes(sym)) return;
    setWatchlist([...watchlist, sym]); // triggers a refetch
    setInput("");
  };

  const total = holdings.data?.reduce((s, h) => s + h.value, 0) ?? 0;
  const cost = holdings.data?.reduce((s, h) => s + (h.cost_basis ?? h.value), 0) ?? 0;
  const gain = total - cost;

  return (
    <Screen loading={holdings.loading} onRefresh={() => { holdings.refresh(); loadQuotes(); }}>
      <LoadState loading={holdings.loading && !holdings.data} error={holdings.error} />
      {holdings.data && (
        <Card>
          <Label>Portfolio</Label>
          <Big>{money(total)}</Big>
          <Text style={{ color: gain >= 0 ? colors.accent : colors.danger }}>
            {gain >= 0 ? "+" : ""}{money(gain)} all-time ({cost ? ((gain / cost) * 100).toFixed(1) : "0"}%)
          </Text>
          {holdings.data.map((h) => (
            <Row key={h.ticker} left={h.ticker} sub={`${h.quantity} sh · ${h.name}`} right={money(h.value)} />
          ))}
        </Card>
      )}

      <Card>
        <Label>Watchlist</Label>
        <View style={{ flexDirection: "row", gap: 8 }}>
          <TextInput
            value={input} onChangeText={setInput} onSubmitEditing={add} placeholder="Add ticker (e.g. MSFT)"
            placeholderTextColor={colors.muted} autoCapitalize="characters"
            style={{ flex: 1, color: colors.text, borderColor: colors.border, borderWidth: 1, borderRadius: 10, padding: 10 }}
          />
          <Pressable onPress={add} style={{ backgroundColor: colors.accent, borderRadius: 10, paddingHorizontal: 16, justifyContent: "center" }}>
            <Text style={{ color: colors.bg, fontWeight: "700" }}>Add</Text>
          </Pressable>
        </View>
        {quotes?.map((q) => <Row key={q.symbol} left={q.symbol} right={<Change q={q} />} />)}
        <Muted>Prices may be delayed.</Muted>
      </Card>
    </Screen>
  );
}
