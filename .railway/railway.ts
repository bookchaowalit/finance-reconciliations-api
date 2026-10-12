import { defineRailway, project, service } from "railway/iac";

// reconciliations: the Reconciliations cell. Variables stay unmanaged (secrets live in Railway only).
// reconciliations-api sleeps when idle (Railway Serverless) and wakes on the next request.
// Every service runs in Singapore next to Neon (aws-ap-southeast-1) and empire-platform; the IaC does not
// carry the region, so after the first deploy: railway scale --service <svc> asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0
export default defineRailway(() => {
  const api = service("reconciliations-api", {
    healthcheck: "/health",
    healthcheckTimeout: 60,
    deploy: { sleepApplication: true },
  });

  return project("reconciliations", {
    variables: { managed: false },
    resources: [api],
  });
});
