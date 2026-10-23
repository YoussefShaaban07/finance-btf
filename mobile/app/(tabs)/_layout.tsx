import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { ComponentProps } from "react";

import { colors } from "@/components/ui";

type IconName = ComponentProps<typeof Ionicons>["name"];

const TABS: { name: string; title: string; icon: IconName }[] = [
  { name: "index", title: "Net Worth", icon: "pie-chart-outline" },
  { name: "cards", title: "Cards", icon: "card-outline" },
  { name: "stocks", title: "Stocks", icon: "trending-up-outline" },
  { name: "wallet", title: "Wallet", icon: "wallet-outline" },
  { name: "chat", title: "Ask Penny", icon: "chatbubble-ellipses-outline" },
];

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: colors.bg },
        headerTintColor: colors.text,
        headerShadowVisible: false,
        tabBarStyle: { backgroundColor: colors.card, borderTopColor: colors.border },
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.muted,
      }}
    >
      {TABS.map((t) => (
        <Tabs.Screen
          key={t.name}
          name={t.name}
          options={{ title: t.title, tabBarIcon: ({ color, size }) => <Ionicons name={t.icon} color={color as string} size={size} /> }}
        />
      ))}
    </Tabs>
  );
}
