import { useRef, useState } from "react";
import { ActivityIndicator, FlatList, KeyboardAvoidingView, Platform, Pressable, Text, TextInput, View } from "react-native";

import { colors } from "@/components/ui";
import { api, ChatMsg } from "@/lib/api";

const STARTERS = [
  "What's my net worth?",
  "Where is most of my money going this month?",
  "Which credit card should I pay off first?",
  "Can I afford a $1,200 laptop right now?",
  "What's a Roth IRA?",
];

export default function ChatScreen() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const list = useRef<FlatList<ChatMsg>>(null);

  const send = async (text = input) => {
    const content = text.trim();
    if (!content || busy) return;
    const next: ChatMsg[] = [...messages, { role: "user", content }];
    setMessages(next);
    setInput("");
    setBusy(true);
    try {
      const r = await api.chat(next);
      setMessages([...next, { role: "assistant", content: r.reply }]);
    } catch (e) {
      setMessages([...next, { role: "assistant", content: `Something went wrong: ${String(e)}` }]);
    } finally {
      setBusy(false);
      setTimeout(() => list.current?.scrollToEnd({ animated: true }), 50);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: colors.bg }} behavior={Platform.OS === "ios" ? "padding" : undefined} keyboardVerticalOffset={90}>
      <FlatList
        ref={list}
        data={messages}
        keyExtractor={(_, i) => String(i)}
        contentContainerStyle={{ padding: 16, gap: 10, flexGrow: 1 }}
        ListEmptyComponent={
          <View style={{ gap: 10 }}>
            <Text style={{ color: colors.text, fontSize: 22, fontWeight: "700" }}>Hey, I'm Penny 👋</Text>
            <Text style={{ color: colors.muted }}>Ask me anything about your money, I can see your accounts, cards, spending and investments.</Text>
            {STARTERS.map((q) => (
              <Pressable key={q} onPress={() => send(q)} style={{ borderColor: colors.border, borderWidth: 1, borderRadius: 12, padding: 12 }}>
                <Text style={{ color: colors.text }}>{q}</Text>
              </Pressable>
            ))}
          </View>
        }
        renderItem={({ item }) => {
          const mine = item.role === "user";
          return (
            <View style={{ alignSelf: mine ? "flex-end" : "flex-start", maxWidth: "85%",
              backgroundColor: mine ? colors.accent : colors.card, borderRadius: 16, padding: 12 }}>
              <Text style={{ color: mine ? colors.bg : colors.text, fontSize: 15, lineHeight: 21 }}>{item.content}</Text>
            </View>
          );
        }}
        ListFooterComponent={busy ? <ActivityIndicator color={colors.muted} style={{ marginTop: 8 }} /> : undefined}
      />
      <Text style={{ color: colors.muted, fontSize: 11, textAlign: "center" }}>Educational info, not financial advice.</Text>
      <View style={{ flexDirection: "row", gap: 8, padding: 12 }}>
        <TextInput
          value={input} onChangeText={setInput} onSubmitEditing={() => send()} placeholder="Ask a money question…"
          placeholderTextColor={colors.muted} returnKeyType="send"
          style={{ flex: 1, color: colors.text, backgroundColor: colors.card, borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10 }}
        />
        <Pressable onPress={() => send()} disabled={busy}
          style={{ backgroundColor: busy ? colors.border : colors.accent, borderRadius: 20, paddingHorizontal: 18, justifyContent: "center" }}>
          <Text style={{ color: colors.bg, fontWeight: "700" }}>Send</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}
