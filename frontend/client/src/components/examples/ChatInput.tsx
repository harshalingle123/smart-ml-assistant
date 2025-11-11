import { ChatInput } from "../ChatInput";

export default function ChatInputExample() {
  return (
    <div className="h-40 flex flex-col justify-end">
      <ChatInput
        onSend={(message, file) => {
          console.log("Message:", message);
          if (file) console.log("File:", file.name);
        }}
      />
    </div>
  );
}
