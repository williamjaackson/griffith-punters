import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";

export default function Home() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1 p-4 flex flex-col items-center justify-center min-h-screen">
        <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 text-center">
          Prediction Markets
        </h1>
        <p className="text-gray-600 text-center mb-8">
          Gamble on anything.
        </p>
        <div className="flex flex-col items-center">
          <div className="bg-white shadow-md rounded-lg p-6 flex flex-col items-center max-w-md">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-12 w-12 text-blue-500 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 20l9-5-9-5-9 5 9 5zm0 0v-8"
          />
        </svg>
        <h2 className="text-xl font-bold mb-2">Tutorial</h2>
        <p className="text-gray-700 text-center">
          Learn how to get started with prediction markets. Place your first bet, track your performance, and join the community!
        </p>
          </div>
        </div>
      </main>
    </SidebarProvider>
  );
}
