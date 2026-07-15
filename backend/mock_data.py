"""
Mock company documents for testing the Knowledge Graph ingestion.

The documents describe a single fictional company, Acme Analytics, and are
written as declarative prose so the LLM graph transformer can extract clean
entities (Employee, Project, Department, Client, OKR, Budget) and relationships
(WORKS_ON, MANAGES, FOCUSED_ON, REPORTS_TO, ALLOCATED_TO, DEPENDS_ON, SERVES).

Each document is ingested separately so the graph can grow incrementally, and
facts intentionally cross-reference one another so both the Librarian
(GraphRAG) and the Boardroom (multi-agent debate) have a richly connected graph
to reason over.
"""

MOCK_DOCUMENTS = [
    {
        "title": "Company Overview & Org Structure",
        "text": """
# Acme Analytics — Company Overview

Acme Analytics is a B2B software company that builds data analytics products for
enterprise customers. The company has roughly 120 employees and is organized into
five departments: Engineering, Product, Finance, Sales, and Customer Success.

## Executive Leadership

Marcus Webb is the CEO and founded Acme Analytics eight years ago.

Sarah Chen is the VP of Engineering and manages the Engineering Department. She
has been with the company for 5 years and reports to Marcus Webb.

Michael Thompson is the VP of Product and manages the Product Department. He
reports to Marcus Webb.

Lisa Wang is the CFO and manages the Finance Department. Finance controls budget
allocations across all projects. Lisa Wang reports to Marcus Webb.

Aisha Patel is the VP of Sales and manages the Sales Department. She reports to
Marcus Webb.

Diego Fernandez is the VP of Customer Success and manages the Customer Success
Department. He reports to Marcus Webb.

## Departments and Budgets

The Engineering Department has a budget of $2.5 million allocated for this fiscal
year and is the largest department by headcount.

The Product Department has a budget of $1.2 million.

The Sales Department has a budget of $900,000.

The Customer Success Department has a budget of $600,000.

The Finance Department does not fund projects directly; instead it approves and
controls how budget is allocated to every project across the company.

## How the Company Operates

Engineering builds and operates the products. Product defines what gets built.
Sales brings in new clients, Customer Success retains and grows them, and Finance
governs spending. Every significant project is sponsored by a department, staffed
by engineers and product managers, and measured against a company OKR.
""",
    },
    {
        "title": "Engineering Team & Reporting Lines",
        "text": """
# Engineering Team — People and Reporting Lines

Sarah Chen leads the Engineering Department. The following engineers make up the
core of the team.

## Backend and Platform

John Martinez is a Senior Software Engineer who reports to Sarah Chen. He works on
Project Alpha and Project Beta and has deep expertise in backend systems and
authentication. John Martinez has been with the company for 3 years and previously
served as the lead engineer on Project Delta.

Priya Nair is a Staff Data Engineer who reports to John Martinez. She works on
Project Beta and specializes in data pipeline reliability.

David Kim is a Junior Developer who reports to John Martinez. He works on Project
Beta and joined the company 6 months ago. David Kim is currently the only frontend
contributor on Project Beta.

Tom Becker is a Site Reliability Engineer who reports to Sarah Chen. He works on
Project Zeta and Project Alpha and owns production uptime and on-call operations.

## Security

Nina Alvarez is a Security Engineer who reports to Sarah Chen. She works on Project
Alpha and leads the company's SOC 2 compliance effort.

## New Initiatives

Rachel Green is an Engineering Manager who reports to Sarah Chen. She manages the
engineering work on Project Gamma and is building out a small team for the planned
education-sector expansion.

## Notes

Backend expertise is concentrated in John Martinez, which the team considers a key
person risk. Sarah Chen has flagged that the Engineering Department is stretched
thin across Project Alpha, Project Beta, and Project Zeta simultaneously.
""",
    },
    {
        "title": "Product Portfolio & Project Status",
        "text": """
# Product Portfolio — Active and Historical Projects

Michael Thompson oversees the Product Department, which manages the following
projects.

## Project Alpha

Project Alpha is a customer-facing web analytics application focused on improving
user engagement. Project Alpha has a status of "In Progress" and is 60% complete.
Emily Rodriguez is the Product Manager who manages Project Alpha, and she reports
to Michael Thompson. Emily Rodriguez joined the company 2 years ago.

Project Alpha is allocated a budget of $800,000 from the Engineering Department.
Project Alpha serves the enterprise client HealthCorp, and it also serves FinServe
Global and RetailNova. Project Alpha depends on Project Zeta for its shared data
platform. Project Alpha is focused on the OKR "Increase user engagement by 40% in
Q2". Sofia Reyes is a Product Designer who works on Project Alpha and reports to
Michael Thompson.

## Project Beta

Project Beta is an internal tool for data analytics and reporting. Project Beta has
a status of "Failing" due to budget constraints and accumulated technical debt.
Project Beta was allocated only $300,000, which the team considers insufficient for
the scope. Project Beta depends on Project Alpha for shared authentication services
and depends on Project Zeta for data. The budget for Project Beta is controlled by
the Finance Department, and Lisa Wang has expressed concerns about continued funding.
Project Beta is focused on the OKR "Reduce operational costs by 15% in Q2".

## Project Gamma

Project Gamma is a new initiative in the planning phase that aims to expand into the
education sector. Kevin O'Brien is the Product Manager who manages Project Gamma and
reports to Michael Thompson. Rachel Green leads the engineering work on Project Gamma.
Project Gamma is being designed to serve the prospective client EduTech Solutions.
Project Gamma is focused on the OKR "Launch 2 new product lines in Q3". No budget has
been allocated to Project Gamma yet, pending approval from Lisa Wang.

## Project Epsilon

Project Epsilon is a mobile companion application for Project Alpha. Project Epsilon
has a status of "In Progress" and is 30% complete. Project Epsilon is managed by Emily
Rodriguez and is allocated a budget of $450,000. Project Epsilon depends on Project
Alpha for its API and serves the client HealthCorp on mobile devices.

## Project Zeta

Project Zeta is the shared data platform and core infrastructure that other products
build on. Project Zeta has a status of "In Progress" and is 75% complete. Project Zeta
is managed by Sarah Chen and is allocated a budget of $1.1 million from the Engineering
Department. Tom Becker works on Project Zeta. Project Alpha and Project Beta both depend
on Project Zeta. Project Zeta is focused on the OKR "Reach 99.9% platform uptime".

## Project Delta (Historical)

Project Delta was a project cancelled last year due to budget overruns. Project Delta
was managed by Emily Rodriguez and had a scope similar to Project Beta. John Martinez
was the lead engineer on Project Delta. The failure of Project Delta made the Finance
Department more cautious about funding new initiatives.
""",
    },
    {
        "title": "Q2–Q3 OKRs & Strategy",
        "text": """
# Objectives and Key Results — Q2 and Q3

Acme Analytics tracks progress against a small set of company-level OKRs. Each OKR is
owned by a project or department.

## Engagement

The OKR "Increase user engagement by 40% in Q2" is focused on by Project Alpha and is
currently at 25% progress. Emily Rodriguez is accountable for this objective. Engagement
metrics are up 18% so far, so hitting 40% will likely require additional contractor
budget.

## Cost Reduction

The OKR "Reduce operational costs by 15% in Q2" is focused on by Project Beta. Because
Project Beta has a failing status, this objective is at risk. If Project Beta is
cancelled, this OKR would fail outright.

## New Product Lines

The OKR "Launch 2 new product lines in Q3" is focused on by Project Gamma. This objective
has not started because Project Gamma has no allocated budget. Kevin O'Brien owns this
objective and is waiting on Lisa Wang's funding decision.

## Reliability

The OKR "Reach 99.9% platform uptime" is focused on by Project Zeta. Tom Becker is
accountable for this objective. Because Project Alpha and Project Beta both depend on
Project Zeta, this reliability target underpins nearly every other product.

## Compliance

The OKR "Achieve SOC 2 Type II certification by end of Q2" is focused on by Project
Alpha. Nina Alvarez leads the work and Emily Rodriguez owns the audit packet, with Sarah
Chen as executive sponsor. HealthCorp requires SOC 2 evidence as a condition of its
contract renewal.

## Revenue

The OKR "Grow annual recurring revenue to $5 million by year end" is owned by the Sales
Department and Aisha Patel. Current annual recurring revenue is approximately $2.4
million across all clients.
""",
    },
    {
        "title": "Finance & Budget Memo — Q2 Planning",
        "text": """
# Finance & Strategy Memo — Q2 Planning

This memo from Lisa Wang and the Finance Department summarizes budget posture for the
quarter.

## Allocation Snapshot

The total company budget for engineering projects is $3 million. Current allocations are
approximately $2.65 million: $800,000 to Project Alpha, $300,000 to Project Beta,
$450,000 to Project Epsilon, and $1.1 million to Project Zeta. Project Gamma remains
unfunded.

Grace Liu is a Financial Analyst who reports to Lisa Wang and maintains these allocation
figures.

## Budget Constraints

The Finance Department, managed by Lisa Wang, has expressed concerns about over-allocation.
Lisa Wang has indicated that Project Beta may be cancelled if it does not show improvement
within 2 months. Cancelling Project Beta would free up $300,000 but would also cause the
"Reduce operational costs by 15% in Q2" OKR to fail.

Sarah Chen has requested an additional $500,000 to fund Project Gamma, but Lisa Wang has
not approved it yet. The approval is pending a business case review scheduled for next
month.

## Vendor and Infrastructure Costs

Cloud hosting for Project Alpha runs $45,000 per month and is trending up due to HealthCorp
traffic spikes. Project Beta's legacy ETL vendor contract renews in August at $120,000
annually unless the team migrates off the platform. Project Zeta's infrastructure spend is
the single largest recurring line item in the Engineering budget.

## Approval Gates

Any budget reallocation above $250,000 requires Lisa Wang's sign-off and a written risk
assessment from Engineering leadership. After the Project Delta post-mortem, all new
project funding also requires a documented business case reviewed by the Finance Department.
""",
    },
    {
        "title": "Clients & Revenue",
        "text": """
# Client Accounts and Revenue

Acme Analytics serves a mix of enterprise and mid-market clients across several industries.

## HealthCorp

HealthCorp is an enterprise client in the healthcare industry. HealthCorp is served by
Project Alpha and by the Project Epsilon mobile application. HealthCorp has been a client
for 2 years and generates $500,000 in annual recurring revenue. Ben Carter is the Account
Executive who serves HealthCorp and reports to Aisha Patel. Hannah Cole is the Customer
Success Manager for HealthCorp and reports to Diego Fernandez. HealthCorp requires SOC 2
Type II evidence before it will renew its contract at the end of Q2.

## FinServe Global

FinServe Global is an enterprise client in the financial services industry. FinServe Global
is served by Project Alpha and generates $1.2 million in annual recurring revenue, making it
the company's largest account. FinServe Global has strict data residency and uptime
requirements that depend directly on Project Zeta.

## RetailNova

RetailNova is a mid-market client in the retail industry. RetailNova is served by Project
Alpha and generates $320,000 in annual recurring revenue. RetailNova is Acme Analytics'
newest client and is considered a reference account for future retail sales.

## EduTech Solutions

EduTech Solutions is a prospective client in the education sector. Project Gamma is being
designed to serve EduTech Solutions. If the deal closes, EduTech Solutions is projected to
generate roughly $400,000 in annual recurring revenue. Closing EduTech Solutions depends on
Project Gamma receiving funding.

## Revenue Summary

Total signed annual recurring revenue is approximately $2.4 million (HealthCorp, FinServe
Global, and RetailNova). Closing EduTech Solutions would move the Sales Department closer to
its $5 million revenue OKR.
""",
    },
    {
        "title": "Risk Register & Historical Context",
        "text": """
# Engineering Risk Register & Historical Context

This register tracks active delivery risks and the lessons carried over from past projects.

## Historical Context — Project Delta

Last year, a project called Project Delta was cancelled due to budget overruns. Project
Delta was managed by Emily Rodriguez and had a scope similar to Project Beta. John Martinez
was the lead engineer on Project Delta and learned valuable lessons about scope management,
which he has tried to apply to Project Beta. The failure of Project Delta made the Finance
Department, led by Lisa Wang, far more cautious about funding new initiatives such as
Project Gamma.

## Project Beta — Active Risks

Risk B-01: Project Beta's authentication dependency on Project Alpha may slip Beta's Q2
milestone if Project Alpha prioritizes HealthCorp and FinServe Global features first.

Risk B-02: Priya Nair flagged that the ETL vendor contract auto-renews at $120,000 unless
the migration completes by July 15.

Risk B-03: David Kim is the only frontend contributor on Project Beta, so the delivery risk
from a single point of failure is high.

Risk B-04: Lisa Wang's cancellation review for Project Beta is scheduled for 8 weeks from now.

## Project Alpha — Active Risks

Risk A-01: HealthCorp requested SSO customization that was not in the original statement of
work, creating scope pressure for John Martinez and Nina Alvarez.

Risk A-02: Engagement metrics are up only 18% against the 40% OKR target, and acceleration
may require contractor budget that Finance has not approved.

Risk A-03: Project Alpha now serves three clients (HealthCorp, FinServe Global, RetailNova),
which increases the blast radius of any outage and raises the stakes on Project Zeta's uptime.

## Project Zeta — Active Risks

Risk Z-01: Because Project Alpha and Project Beta both depend on Project Zeta, any downtime in
Project Zeta cascades to customer-facing products and threatens the 99.9% uptime OKR.

Risk Z-02: Tom Becker is on-call for both Project Zeta and Project Alpha, which the team
considers unsustainable staffing.

## Compliance & Operations

HealthCorp requires SOC 2 evidence by end of Q2. Nina Alvarez leads the effort and Emily
Rodriguez owns the audit packet, with Sarah Chen as executive sponsor. After the Project
Delta post-mortem, all production changes for Project Beta must go through Finance-approved
change windows.

## Incident Log (Summary)

March: Project Beta's pipeline failed for 6 hours during month-end close; the root cause was
an undocumented schema change in a source CRM export.

April: Project Alpha had a deployment rollback due to a feature-flag misconfiguration, with no
client data impact.

May: Project Zeta experienced 20 minutes of degraded performance that briefly affected
Project Alpha; Tom Becker led the remediation.
""",
    },
]


def get_mock_documents() -> list[dict[str, str]]:
    """Return mock documents as title/text pairs."""
    return MOCK_DOCUMENTS

# Made with Bob
