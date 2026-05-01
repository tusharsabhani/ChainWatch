import { LoadingState } from "@/components/states/loading-state";

export default function Loading() {
  return (
    <div className="space-y-4 p-4 lg:p-8">
      <LoadingState
        title="Loading ChainWatch"
        description="Preparing the route shell and checking the backend surface."
      />
    </div>
  );
}
