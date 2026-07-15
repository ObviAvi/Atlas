# Project Omega — Real-Time Alerting & West Coast Expansion Brief

This brief introduces Project Omega, a new engineering initiative at Acme Analytics,
and documents the new hires, client commitments, budget requests, and risks that come
with it. It is written to extend the existing company knowledge graph, so it references
existing people, projects, clients, and OKRs directly.

## Overview

Project Omega is a new real-time alerting and anomaly-detection product that sits on top
of the shared data platform. Project Omega has a status of "In Progress" and is 20%
complete. Project Omega is sponsored by the Engineering Department and is intended to
become Acme Analytics' first product sold primarily to the logistics and operations
market.

Project Omega depends on Project Zeta for its streaming data platform, and it depends on
Project Alpha for shared authentication and single sign-on services. Because Project
Omega consumes live event streams from Project Zeta, its reliability is tightly coupled
to the "Reach 99.9% platform uptime" OKR that Project Zeta already owns.

## People and Reporting Lines

Rachel Green is the Engineering Manager who manages the engineering work on Project Omega,
in addition to her existing work on Project Gamma. Rachel Green reports to Sarah Chen.

Omar Haddad is a Senior Backend Engineer who was hired to reduce the key-person risk
concentrated in John Martinez. Omar Haddad reports to Sarah Chen, works on Project Omega,
and also works on Project Zeta. Omar Haddad has deep expertise in event streaming and
distributed systems, and he is expected to share on-call duties with Tom Becker so that
Tom Becker is no longer the sole on-call engineer for Project Zeta and Project Alpha.

Chloe Bennett is a Product Manager who manages Project Omega and reports to Michael
Thompson. Chloe Bennett joined the company 3 months ago from a logistics-software
competitor and previously shipped a real-time alerting product.

Priya Nair, the Staff Data Engineer who works on Project Beta, is being consulted part
time on Project Omega for data-pipeline design, since Project Omega and Project Beta both
read from Project Zeta. Priya Nair continues to report to John Martinez.

## Clients Served

Project Omega serves LogiCore, a new enterprise client in the logistics industry.
LogiCore has signed a contract that generates $650,000 in annual recurring revenue,
which would make LogiCore the second-largest account after FinServe Global. LogiCore
requires sub-minute alerting on shipment anomalies and has strict uptime requirements
that depend directly on Project Zeta.

Project Omega also serves FinServe Global, which has requested real-time fraud alerts as
an add-on to its existing Project Alpha analytics. Because FinServe Global already depends
on Project Zeta through Project Alpha, adding Project Omega increases FinServe Global's
exposure to any Project Zeta outage.

Ben Carter is the Account Executive who serves LogiCore and reports to Aisha Patel. Ben
Carter also serves HealthCorp. Hannah Cole is the Customer Success Manager assigned to
LogiCore and reports to Diego Fernandez.

## Budget and Approvals

Sarah Chen has requested a budget of $700,000 for Project Omega, to be allocated from the
Engineering Department. Because this request is above the $250,000 approval gate, it
requires Lisa Wang's sign-off and a written risk assessment from Engineering leadership.
Lisa Wang has not yet approved the Project Omega budget; the decision is scheduled
alongside the pending Project Gamma funding review.

Grace Liu, the Financial Analyst who reports to Lisa Wang, has noted that approving both
Project Omega ($700,000) and Project Gamma ($500,000) would push total engineering
allocations past the $3 million ceiling unless Project Beta is cancelled to free up its
$300,000. This directly connects the Project Omega decision to the "Reduce operational
costs by 15% in Q2" OKR that Project Beta owns.

## OKRs

Project Omega is focused on a new OKR, "Sign 3 logistics clients by end of Q4", owned by
the Sales Department and Aisha Patel. LogiCore is the first of the three target accounts.

Project Omega also contributes to the existing OKR "Grow annual recurring revenue to $5
million by year end", because the LogiCore contract adds $650,000 in annual recurring
revenue on top of the roughly $2.4 million already signed from HealthCorp, FinServe
Global, and RetailNova.

## Risks

Risk O-01: Project Omega increases the load on Project Zeta, which is already at 75%
completion and underpins Project Alpha and Project Beta. Any Project Zeta capacity
shortfall now cascades to a third product and a new revenue-critical client, LogiCore.

Risk O-02: Omar Haddad is a brand-new hire, so the intended relief of the John Martinez
key-person risk will not fully materialize until Omar Haddad has ramped up, estimated at
two to three months.

Risk O-03: LogiCore's sub-minute alerting requirement is more aggressive than anything
Project Zeta currently guarantees, so the 99.9% uptime OKR may need to be tightened for
Project Omega workloads specifically.

Risk O-04: Because the Project Omega and Project Gamma budget decisions are coupled and
both sit above the $250,000 approval gate, a delay in Lisa Wang's review blocks both
initiatives at once. After the Project Delta post-mortem, each still requires a documented
business case reviewed by the Finance Department.

## Historical Context

Chloe Bennett has explicitly compared Project Omega's scope-management plan to the lessons
from Project Delta, the project that was cancelled last year due to budget overruns and
managed by Emily Rodriguez. To avoid repeating Project Delta's failure, Project Omega will
be delivered in three funded phases, each gated by a Finance-approved business case rather
than a single large allocation.
