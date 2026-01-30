# Knowledge Graph Architecture

**Purpose**: Define how filings, entities, and relationships connect into a queryable knowledge graph.

---

## The Vision

```
                    ┌─────────────────────────────────────────┐
                    │         KNOWLEDGE GRAPH                  │
                    │                                         │
   NVIDIA 10-K ────▶│   [NVIDIA] ──supplies──▶ [TSMC]        │
                    │       │                    │            │
   Apple 10-K ─────▶│       │                    │            │
                    │   competes              supplies        │
                    │       │                    │            │
   TSMC 20-F ──────▶│       ▼                    ▼            │
                    │   [Apple] ◀──supplies── [Foxconn]      │
                    │                                         │
                    └─────────────────────────────────────────┘
                                      │
                                      ▼
                         "Find all companies that supply
                          to both NVIDIA and Apple"
```

---

## Graph Model

### Nodes

```python
from enum import Enum
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Any

class NodeType(Enum):
    """Types of nodes in the knowledge graph."""
    COMPANY = "company"
    PERSON = "person"
    PRODUCT = "product"
    INDUSTRY = "industry"
    FILING = "filing"
    RISK = "risk"
    EVENT = "event"


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    node_id: str
    node_type: NodeType
    name: str

    # Properties vary by type
    properties: Dict[str, Any]

    # Source tracking
    source_filings: List[str]  # accession_numbers
    first_seen: date
    last_seen: date
    mention_count: int


@dataclass
class CompanyNode(GraphNode):
    """Company node with specific properties."""
    node_type: NodeType = NodeType.COMPANY

    # Identifiers
    cik: str | None = None
    ticker: str | None = None
    entity_id: str | None = None  # EntitySpine ID

    # Attributes
    sic_code: str | None = None
    industry: str | None = None
    sector: str | None = None
    market_cap: float | None = None

    # Filing count
    filings_count: int = 0


@dataclass
class PersonNode(GraphNode):
    """Person node (executives, board members)."""
    node_type: NodeType = NodeType.PERSON

    # Roles
    current_company: str | None = None
    current_role: str | None = None

    # History
    role_history: List[Dict] = None  # [{company, role, start, end}]


@dataclass
class ProductNode(GraphNode):
    """Product or service node."""
    node_type: NodeType = NodeType.PRODUCT

    # Ownership
    company_id: str

    # Attributes
    category: str | None = None
    launch_date: date | None = None
```

### Edges (Relationships)

```python
class RelationshipType(Enum):
    """Types of relationships between nodes."""

    # Company-Company
    SUPPLIES_TO = "supplies_to"
    CUSTOMER_OF = "customer_of"
    COMPETES_WITH = "competes_with"
    PARTNERS_WITH = "partners_with"
    SUBSIDIARY_OF = "subsidiary_of"
    PARENT_OF = "parent_of"
    ACQUIRED = "acquired"
    ACQUIRED_BY = "acquired_by"
    INVESTED_IN = "invested_in"

    # Company-Person
    EMPLOYS = "employs"
    BOARD_MEMBER = "board_member"

    # Company-Product
    PRODUCES = "produces"
    USES = "uses"

    # Company-Industry
    OPERATES_IN = "operates_in"

    # Company-Risk
    HAS_RISK = "has_risk"

    # Company-Filing
    FILED = "filed"


@dataclass
class GraphEdge:
    """A relationship between two nodes."""
    edge_id: str
    source_id: str
    target_id: str
    relationship: RelationshipType

    # Properties
    properties: Dict[str, Any]

    # Evidence
    evidence: List["EdgeEvidence"]
    confidence: float  # 0.0 - 1.0

    # Temporal
    first_seen: date
    last_seen: date
    mention_count: int


@dataclass
class EdgeEvidence:
    """Evidence for a relationship from a specific filing."""
    accession_number: str
    section: str
    text_excerpt: str
    extraction_method: str  # "ner", "pattern", "llm"
    confidence: float
    extracted_at: datetime
```

---

## Graph Storage (DuckDB)

### Schema

```sql
-- Nodes table
CREATE TABLE graph_nodes (
    node_id VARCHAR PRIMARY KEY,
    node_type VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    properties JSON,

    -- For companies
    cik VARCHAR,
    ticker VARCHAR,
    entity_id VARCHAR,
    sic_code VARCHAR,

    -- Tracking
    first_seen DATE,
    last_seen DATE,
    mention_count INTEGER DEFAULT 1,

    INDEX idx_type (node_type),
    INDEX idx_name (name),
    INDEX idx_cik (cik),
    INDEX idx_ticker (ticker),
);

-- Edges table
CREATE TABLE graph_edges (
    edge_id VARCHAR PRIMARY KEY,
    source_id VARCHAR NOT NULL REFERENCES graph_nodes(node_id),
    target_id VARCHAR NOT NULL REFERENCES graph_nodes(node_id),
    relationship VARCHAR NOT NULL,

    properties JSON,
    confidence FLOAT,

    first_seen DATE,
    last_seen DATE,
    mention_count INTEGER DEFAULT 1,

    INDEX idx_source (source_id),
    INDEX idx_target (target_id),
    INDEX idx_relationship (relationship),
    UNIQUE(source_id, target_id, relationship),
);

-- Edge evidence table
CREATE TABLE edge_evidence (
    id INTEGER PRIMARY KEY,
    edge_id VARCHAR NOT NULL REFERENCES graph_edges(edge_id),
    accession_number VARCHAR NOT NULL,
    section VARCHAR,
    text_excerpt TEXT,
    extraction_method VARCHAR,
    confidence FLOAT,
    extracted_at TIMESTAMP,
);

-- Materialized view for quick traversal
CREATE TABLE graph_adjacency AS
SELECT
    source_id,
    target_id,
    relationship,
    confidence
FROM graph_edges
WHERE confidence > 0.5;
```

### Graph Builder

```python
class KnowledgeGraphBuilder:
    """Build knowledge graph from enriched filings."""

    def __init__(self, graph_store: GraphStore):
        self.store = graph_store

    def add_filing(self, filing: EnrichedFiling) -> None:
        """Add a filing's entities and relationships to the graph."""

        # 1. Add/update filer node
        filer_node = self._get_or_create_company_node(
            name=filing.company.name,
            cik=filing.company.cik,
            ticker=filing.company.ticker,
        )

        # 2. Add filing node
        filing_node = GraphNode(
            node_id=f"filing:{filing.identity.accession_number}",
            node_type=NodeType.FILING,
            name=f"{filing.company.ticker} {filing.identity.form_type} {filing.identity.filed_date}",
            properties={
                "accession_number": filing.identity.accession_number,
                "form_type": filing.identity.form_type,
                "filed_date": str(filing.identity.filed_date),
            },
        )
        self.store.save_node(filing_node)

        # 3. Link filer to filing
        self.store.save_edge(GraphEdge(
            source_id=filer_node.node_id,
            target_id=filing_node.node_id,
            relationship=RelationshipType.FILED,
            confidence=1.0,
        ))

        # 4. Add entity relationships
        for mention in filing.entities.suppliers:
            self._add_relationship(
                filer_node,
                mention,
                RelationshipType.CUSTOMER_OF,  # We are customer of supplier
                filing,
            )

        for mention in filing.entities.customers:
            self._add_relationship(
                filer_node,
                mention,
                RelationshipType.SUPPLIES_TO,  # We supply to customer
                filing,
            )

        for mention in filing.entities.competitors:
            self._add_relationship(
                filer_node,
                mention,
                RelationshipType.COMPETES_WITH,
                filing,
            )

        for mention in filing.entities.subsidiaries:
            self._add_relationship(
                filer_node,
                mention,
                RelationshipType.PARENT_OF,
                filing,
            )

    def _add_relationship(
        self,
        source: GraphNode,
        mention: EntityMention,
        relationship: RelationshipType,
        filing: EnrichedFiling,
    ) -> None:
        """Add or update a relationship."""

        # Get or create target node
        target = self._get_or_create_company_node(
            name=mention.name,
            cik=mention.resolved_cik,
            entity_id=mention.resolved_entity_id,
        )

        # Create or update edge
        edge_id = f"{source.node_id}:{target.node_id}:{relationship.value}"
        existing = self.store.get_edge(edge_id)

        if existing:
            # Update existing edge
            existing.mention_count += 1
            existing.last_seen = filing.identity.filed_date
            if mention.confidence > existing.confidence:
                existing.confidence = mention.confidence
            self.store.save_edge(existing)
        else:
            # Create new edge
            edge = GraphEdge(
                edge_id=edge_id,
                source_id=source.node_id,
                target_id=target.node_id,
                relationship=relationship,
                confidence=mention.confidence,
                first_seen=filing.identity.filed_date,
                last_seen=filing.identity.filed_date,
                mention_count=1,
                evidence=[],
            )
            self.store.save_edge(edge)

        # Add evidence
        evidence = EdgeEvidence(
            accession_number=filing.identity.accession_number,
            section=mention.section,
            text_excerpt=mention.surrounding_text,
            extraction_method=mention.extraction_method,
            confidence=mention.confidence,
            extracted_at=datetime.now(UTC),
        )
        self.store.save_evidence(edge_id, evidence)
```

---

## Graph Queries

### Query Interface

```python
class KnowledgeGraphQuery:
    """Query the knowledge graph."""

    def __init__(self, store: GraphStore):
        self.store = store

    # ==========================================================================
    # DIRECT RELATIONSHIPS
    # ==========================================================================

    def find_suppliers(
        self,
        company: str,  # Ticker, CIK, or name
        min_confidence: float = 0.5,
        limit: int = 50,
    ) -> List[RelatedCompany]:
        """Find suppliers of a company."""
        node = self._resolve_company(company)
        return self.store.query_edges(
            source_id=node.node_id,
            relationship=RelationshipType.CUSTOMER_OF,
            min_confidence=min_confidence,
            limit=limit,
        )

    def find_customers(
        self,
        company: str,
        min_confidence: float = 0.5,
        limit: int = 50,
    ) -> List[RelatedCompany]:
        """Find customers of a company."""
        node = self._resolve_company(company)
        return self.store.query_edges(
            source_id=node.node_id,
            relationship=RelationshipType.SUPPLIES_TO,
            min_confidence=min_confidence,
            limit=limit,
        )

    def find_competitors(
        self,
        company: str,
        min_confidence: float = 0.5,
        limit: int = 50,
    ) -> List[RelatedCompany]:
        """Find competitors of a company."""
        node = self._resolve_company(company)
        return self.store.query_edges(
            source_id=node.node_id,
            relationship=RelationshipType.COMPETES_WITH,
            min_confidence=min_confidence,
            limit=limit,
        )

    # ==========================================================================
    # SUPPLY CHAIN ANALYSIS
    # ==========================================================================

    def analyze_supply_chain(
        self,
        company: str,
        depth: int = 2,  # How many hops
    ) -> SupplyChainAnalysis:
        """Analyze a company's supply chain."""
        node = self._resolve_company(company)

        # BFS to find supply chain
        suppliers = self._traverse(
            node.node_id,
            RelationshipType.CUSTOMER_OF,
            depth=depth,
        )

        customers = self._traverse(
            node.node_id,
            RelationshipType.SUPPLIES_TO,
            depth=depth,
        )

        # Calculate concentration
        critical = [s for s in suppliers if s.is_critical]

        return SupplyChainAnalysis(
            company=node.name,
            suppliers=suppliers,
            customers=customers,
            critical_suppliers=critical,
            concentration_risk=self._calc_concentration(suppliers),
            geographic_exposure=self._calc_geo_exposure(suppliers),
        )

    def find_common_suppliers(
        self,
        companies: List[str],
    ) -> List[CompanyNode]:
        """Find suppliers shared by multiple companies."""
        supplier_sets = []
        for company in companies:
            suppliers = self.find_suppliers(company)
            supplier_sets.append({s.node_id for s in suppliers})

        common = set.intersection(*supplier_sets)
        return [self.store.get_node(nid) for nid in common]

    def find_supply_chain_risks(
        self,
        company: str,
    ) -> List[SupplyChainRisk]:
        """Identify supply chain risks."""
        analysis = self.analyze_supply_chain(company, depth=2)

        risks = []

        # Single source risk
        for supplier in analysis.critical_suppliers:
            if supplier.is_single_source:
                risks.append(SupplyChainRisk(
                    type="single_source",
                    entity=supplier.name,
                    severity="high",
                    description=f"{supplier.name} is single source for critical component",
                ))

        # Geographic concentration
        for region, pct in analysis.geographic_exposure.items():
            if pct > 0.5:  # >50% from one region
                risks.append(SupplyChainRisk(
                    type="geographic_concentration",
                    entity=region,
                    severity="medium",
                    description=f"{pct:.0%} of supply chain in {region}",
                ))

        return risks

    # ==========================================================================
    # PATH FINDING
    # ==========================================================================

    def find_path(
        self,
        source: str,
        target: str,
        max_depth: int = 4,
    ) -> List[GraphPath]:
        """Find paths between two companies."""
        source_node = self._resolve_company(source)
        target_node = self._resolve_company(target)

        # BFS for shortest paths
        paths = self._find_paths_bfs(
            source_node.node_id,
            target_node.node_id,
            max_depth=max_depth,
        )

        return [
            GraphPath(
                nodes=[self.store.get_node(nid) for nid in path],
                edges=[self.store.get_edge(eid) for eid in path_edges],
                length=len(path) - 1,
            )
            for path, path_edges in paths
        ]

    def find_connections(
        self,
        company: str,
        max_depth: int = 2,
    ) -> List[GraphNode]:
        """Find all connected entities within N hops."""
        node = self._resolve_company(company)

        visited = {node.node_id}
        current_level = [node.node_id]

        for _ in range(max_depth):
            next_level = []
            for nid in current_level:
                neighbors = self.store.get_neighbors(nid)
                for neighbor in neighbors:
                    if neighbor.node_id not in visited:
                        visited.add(neighbor.node_id)
                        next_level.append(neighbor.node_id)
            current_level = next_level

        return [self.store.get_node(nid) for nid in visited]

    # ==========================================================================
    # INDUSTRY / SECTOR ANALYSIS
    # ==========================================================================

    def get_industry_graph(
        self,
        sic_code: str,
        min_filings: int = 1,
    ) -> IndustryGraph:
        """Get relationship graph for an industry."""
        # Find all companies in industry
        companies = self.store.query_nodes(
            node_type=NodeType.COMPANY,
            filters={"sic_code": sic_code},
        )

        # Get all edges between them
        company_ids = {c.node_id for c in companies}
        edges = self.store.query_edges(
            source_ids=company_ids,
            target_ids=company_ids,
        )

        return IndustryGraph(
            sic_code=sic_code,
            companies=companies,
            relationships=edges,
        )

    def compare_peer_networks(
        self,
        companies: List[str],
    ) -> PeerComparison:
        """Compare supplier/customer networks of peer companies."""
        networks = {}
        for company in companies:
            node = self._resolve_company(company)
            networks[company] = {
                "suppliers": set(s.name for s in self.find_suppliers(company)),
                "customers": set(c.name for c in self.find_customers(company)),
                "competitors": set(c.name for c in self.find_competitors(company)),
            }

        return PeerComparison(
            companies=companies,
            networks=networks,
            common_suppliers=set.intersection(*[n["suppliers"] for n in networks.values()]),
            common_customers=set.intersection(*[n["customers"] for n in networks.values()]),
        )
```

---

## Usage Examples

```python
from py_sec_edgar import SEC

async with SEC() as sec:
    # Build graph from downloaded filings
    await sec.build_graph()

    # Query relationships
    suppliers = await sec.graph.find_suppliers("NVDA")
    print("NVIDIA's suppliers:")
    for s in suppliers[:10]:
        print(f"  {s.name} (confidence: {s.confidence:.2f})")

    # Supply chain analysis
    analysis = await sec.graph.analyze_supply_chain("AAPL")
    print(f"\nApple supply chain:")
    print(f"  Critical suppliers: {[s.name for s in analysis.critical_suppliers]}")
    print(f"  Concentration risk: {analysis.concentration_risk}")

    # Find common suppliers
    common = await sec.graph.find_common_suppliers(["NVDA", "AMD", "INTC"])
    print(f"\nCommon chip company suppliers: {[c.name for c in common]}")

    # Path finding
    paths = await sec.graph.find_path("NVDA", "TSMC")
    print(f"\nPath from NVIDIA to TSMC:")
    for path in paths[:3]:
        print(f"  {' -> '.join(n.name for n in path.nodes)}")

    # Industry analysis
    tech_graph = await sec.graph.get_industry_graph(sic_code="3571")
    print(f"\nTech hardware industry: {len(tech_graph.companies)} companies")
```

---

## Graph Visualization Data

For frontend visualization, export graph data:

```python
def export_for_visualization(
    graph_query: KnowledgeGraphQuery,
    company: str,
    depth: int = 2,
) -> dict:
    """Export graph data for D3.js/Cytoscape visualization."""

    # Get connected nodes
    nodes = graph_query.find_connections(company, max_depth=depth)

    # Get all edges between them
    node_ids = {n.node_id for n in nodes}
    edges = graph_query.store.query_edges(
        source_ids=node_ids,
        target_ids=node_ids,
    )

    return {
        "nodes": [
            {
                "id": n.node_id,
                "label": n.name,
                "type": n.node_type.value,
                "properties": n.properties,
                "size": n.mention_count,
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": e.edge_id,
                "source": e.source_id,
                "target": e.target_id,
                "type": e.relationship.value,
                "confidence": e.confidence,
                "weight": e.mention_count,
            }
            for e in edges
        ],
    }
```

---

## Next Steps

- [05_LLM_INTEGRATION.md](05_LLM_INTEGRATION.md) - AI-powered extraction
- [06_FRONTEND_VISUALIZATION.md](06_FRONTEND_VISUALIZATION.md) - React graph UI
