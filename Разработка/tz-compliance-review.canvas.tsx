import { Divider, Grid, H1, H2, Stack, Stat, Table, Text } from 'cursor/canvas';

const findings = [
  ['Medium', 'bot_service lint', 'ruff fails on unused import json in app/tasks/llm_tasks.py', 'Fix before final submission'],
  ['Medium', 'User auth UX', 'Manual JWT via /token matches current TZ, but is weak for real users', 'Already recorded as P0 backlog'],
  ['Low', 'README structure', 'Root README still mentions service .env.example paths while compose uses project-level env examples', 'Polish docs if time allows'],
  ['Low', 'Operations', 'No production-grade dead-letter queue or monitoring for max:outbox', 'Acceptable for v1, note as production risk'],
];

const coverage = [
  ['Auth Service', 'Compliant', 'register/login/me, bcrypt, JWT sub/role/iat/exp, repository/usecase split'],
  ['Bot Service', 'Compliant', 'MAX handlers, local JWT validation, Redis max_auth/user_chat mapping'],
  ['Async LLM', 'Compliant', 'RabbitMQ/Celery task llm_request(sub, role, prompt), OpenRouter client'],
  ['Delivery', 'Compliant', 'Redis LIST max:outbox, BLPOP consumer, MAX API only in Bot Service'],
  ['Tests', 'Compliant', 'auth 12/12 passed, bot 20/20 passed'],
  ['Lint', 'Needs fix', 'auth ruff passed, bot ruff has one unused import'],
];

export default function TzComplianceReview() {
  return (
    <Stack gap={20}>
      <H1>TZ Compliance Review</H1>
      <Text>
        Architectural review of the MAX LLM consultation project against TЗ_МАКС.txt and Arch.txt.
      </Text>

      <Grid columns={4} gap={16}>
        <Stat value="High" label="Overall Compliance" tone="success" />
        <Stat value="32/32" label="Tests Passed" tone="success" />
        <Stat value="1" label="Blocking Quality Issue" tone="warning" />
        <Stat value="0" label="Critical Architecture Breaks" tone="success" />
      </Grid>

      <Divider />

      <H2>Component Coverage</H2>
      <Table
        headers={['Area', 'Status', 'Evidence']}
        rows={coverage}
        rowTone={['success', 'success', 'success', 'success', 'success', 'warning']}
      />

      <Divider />

      <H2>Findings</H2>
      <Table
        headers={['Severity', 'Area', 'Finding', 'Recommendation']}
        rows={findings}
        rowTone={['warning', 'warning', undefined, undefined]}
      />

      <Divider />

      <H2>Verdict</H2>
      <Text>
        The implementation is suitable for educational acceptance after fixing the single lint issue.
        The architecture follows the approved deviation: Redis stores derived auth state, Celery writes
        to outbox, and MAX delivery stays inside Bot Service.
      </Text>
    </Stack>
  );
}
