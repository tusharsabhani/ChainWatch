export type ErrorDetail = {
  code: string;
  message: string;
  details: Record<string, unknown>;
};

export type ErrorResponse = {
  error: ErrorDetail;
};

export type FreshnessInfo = {
  dataSource: string;
  lastUpdatedAt: string | null;
  cacheUpdatedAt: string | null;
  isStale: boolean;
  refreshScheduled: boolean;
};

export type HealthResponse = {
  status: string;
  appVersion: string;
  database: {
    status: string;
    path: string;
  };
  storage: {
    reportsJsonPath: string;
    reportsMarkdownPath: string;
    importsPath: string;
    cachePath: string;
  };
  providers: {
    llmConfigured: boolean;
    searchConfigured: boolean;
  };
  backgroundTasks: {
    reportsEnabled: boolean;
    externalRiskRefreshEnabled: boolean;
  };
};

export type DashboardSummaryQuery = {
  dateRange?: "7d" | "30d" | "90d";
  severityMin?: 1 | 2 | 3 | 4 | 5;
  category?: string;
  region?: string;
};

export type DashboardSummaryResponse = {
  filters: {
    dateRange: string;
    severityMin: number;
    category: string | null;
    region: string | null;
  };
  kpis: {
    activeAlerts: number;
    productsAtRisk: number;
    suppliersExposed: number;
    countriesWithIssues: number;
  };
  topRiskProducts: Array<{
    productId: number;
    sku: string;
    name: string;
    riskScore: number;
    primaryRiskDriver: string;
  }>;
  topRiskSuppliers: Array<{
    supplierId: number;
    name: string;
    countryCode: string;
    riskScore: number;
    activeIssueCount: number;
  }>;
  countryExposure: Array<{
    countryCode: string;
    overallScore: number;
    activeEventCount: number;
  }>;
  trends: {
    demandPressure: Array<{ label: string; value: number }>;
    slaRisk: Array<{ label: string; value: number }>;
    externalEventCount: Array<{ label: string; value: number }>;
  };
  lastUpdatedAt: string;
  freshness: FreshnessInfo | null;
};

export type DashboardAlertsQuery = {
  severityMin?: 1 | 2 | 3 | 4 | 5;
  status?: "open" | "monitoring" | "resolved";
  limit?: number;
};

export type DashboardAlertsResponse = {
  items: Array<{
    eventId: string;
    title: string;
    riskType: string;
    severity: number;
    countryCode: string | null;
    affectedSupplierId: number | null;
    affectedProductId: number | null;
    status: string;
    detectedAt: string;
  }>;
  total: number;
  lastUpdatedAt: string;
  freshness: FreshnessInfo | null;
};

export type MapCountriesResponse = {
  items: Array<{
    countryCode: string;
    countryName: string;
    overallScore: number;
    highestSeverity: number;
    activeEventCount: number;
  }>;
  lastUpdatedAt: string;
  freshness: FreshnessInfo | null;
};

export type MapCountriesQuery = {
  riskType?: string;
  severityMin?: 1 | 2 | 3 | 4 | 5;
};

export type CountryDetailResponse = {
  country: {
    countryCode: string;
    countryName: string;
    overallScore: number;
    summary: string;
  };
  issues: Array<{
    eventId: string;
    title: string;
    riskType: string;
    severity: number;
    sourceUrl: string | null;
  }>;
  affectedSuppliers: Array<{
    supplierId: number;
    name: string;
  }>;
  affectedProducts: Array<{
    productId: number;
    sku: string;
    name: string;
  }>;
  lastUpdatedAt: string | null;
  freshness: FreshnessInfo | null;
};

export type ProductListResponse = {
  items: Array<{
    productId: number;
    sku: string;
    name: string;
    category: string;
    riskScore: number;
  }>;
};

export type ProductListQuery = {
  query?: string;
  category?: string;
  riskMin?: number;
  limit?: number;
};

export type ProductDetailResponse = {
  product: {
    id: number;
    sku: string;
    name: string;
    category: string;
    brand: string | null;
  };
  demand: {
    demandRiskScore: number;
    historicalTrend: Array<Record<string, unknown>>;
    seasonalWindows: Array<Record<string, unknown>>;
    recentSpikes: Array<Record<string, unknown>>;
  };
  inventory: {
    currentOnHand: number;
    reservedQty: number;
    inboundQty: number;
    daysOfCover: number | null;
    stockoutRiskScore: number;
    recommendedAction: string;
  };
  fulfillment: {
    fulfillmentRiskScore: number;
    backlogOrders: number;
    avgShipDelayHours: number;
    onTimeRate: number;
  };
  suppliers: Array<{
    supplierId: number;
    supplierCode: string;
    name: string;
    countryCode: string;
    region: string | null;
    leadTimeDays: number | null;
    reliabilityScore: number | null;
  }>;
  linkedRiskEvents: Array<{
    eventId: string;
    title: string;
    riskType: string;
    severity: number;
    countryCode: string | null;
    sourceUrl: string | null;
  }>;
  lastUpdatedAt: string | null;
  freshness: FreshnessInfo | null;
};

export type ProductDetailQuery = {
  dateRange?: "30d" | "90d" | "365d";
  region?: string;
  channel?: string;
};

export type ChatSessionsResponse = {
  items: Array<{
    id: string;
    title: string;
    contextScope: string;
    contextId: string | null;
    updatedAt: string;
  }>;
};

export type ChatCreateSessionRequest = {
  title?: string | null;
  contextScope?: string;
  contextId?: string | null;
};

export type ChatCreateSessionResponse = {
  id: string;
  title: string;
  contextScope: string;
  contextId: string | null;
  createdAt: string;
};

export type ChatMessagesResponse = {
  session: {
    id: string;
    title: string;
  };
  messages: Array<{
    id: string;
    role: string;
    messageText: string;
    citations: Array<{
      title: string;
      url: string;
      sourceName: string;
      snippet: string | null;
    }> | null;
    usedAgents: string[] | null;
    limitations: string[] | null;
    createdAt: string;
  }>;
};

export type ChatPostMessageRequest = {
  sessionId: string;
  message: string;
};

export type ChatPostMessageResponse = {
  userMessage: ChatMessagesResponse["messages"][number];
  assistantMessage: ChatMessagesResponse["messages"][number];
};

export type ReportsListResponse = {
  items: Array<{
    id: string;
    title: string;
    scopeType: string;
    status: string;
    createdAt: string;
    markdownPath: string | null;
  }>;
};

export type ReportsListQuery = {
  scopeType?: string;
  status?: string;
  limit?: number;
};

export type ReportDetailResponse = {
  id: string;
  title: string;
  scopeType: string;
  scopeId: string | null;
  status: string;
  summary: string | null;
  jsonPath: string | null;
  markdownPath: string | null;
  markdownPreview: string | null;
  createdAt: string;
  completedAt: string | null;
  freshness: FreshnessInfo | null;
};

export type ReportGenerateRequest = {
  scopeType: string;
  scopeId?: string | null;
  reportType: string;
  title?: string | null;
};

export type ReportGenerateResponse = {
  id: string;
  status: string;
  scopeType: string;
  scopeId: string | null;
  createdAt: string;
};

export type ImportsListResponse = {
  items: Array<{
    id: string;
    importType: string;
    filename: string;
    status: string;
    rowCount: number;
    insertedCount: number;
    errorCount: number;
    completedAt: string | null;
  }>;
};

export type ImportStartRequest = {
  filePath: string;
};

export type ImportStartResponse = {
  id: string;
  importType: string;
  status: string;
};
