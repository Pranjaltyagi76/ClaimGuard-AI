# Motivation

## The real-world spark

A close friend's father runs a **mobile-phone showroom in Ghaziabad**. He kept
running into the same quiet, expensive problem: customers filing device-damage
insurance claims using **fake or recycled photos** — an image of a cracked
screen that isn't their phone, or an old photo of damage that was already
claimed once. A busy shop counter cannot forensically inspect every image, so a
meaningful fraction of fraudulent claims slip through and someone eats the loss.

The insight that started this project:

> The **images are the actual evidence**, but nobody has the time or tooling to
> reason about them carefully — which is exactly what a vision-language model is
> good at.

## Why this problem is worth solving

- **It's real and specific.** This is not a toy prompt; it's a loss that happens
  at counters and insurer back-offices every week.
- **It's high-stakes and adjacent to money.** A wrong "approve" pays out fraud;
  a wrong "reject" angers an honest customer. The right behavior when unsure is
  to **escalate to a human**, not to guess.
- **It's a natural fit for agentic + multimodal AI.** Reading a claim,
  inspecting photos, cross-checking evidence, and flagging risk decomposes
  cleanly into cooperating agents.

## Guiding principles

1. **Images are the primary source of truth.** The claim text says *what to
   check*; the image says *what is real*.
2. **Honesty over confidence.** The system must be able to say
   `not_enough_information` and route to manual review rather than fabricate a
   verdict.
3. **Cost- and latency-aware.** Only the stage that needs a model (vision) makes
   a model call; everything else is deterministic.
4. **Auditability.** Every verdict comes with a plain-English, image-grounded
   justification a human reviewer can check.

## Who benefits

- **Device retailers / showrooms** — first-line fraud screening.
- **Insurers / TPAs** — triage claims, cut manual review load, catch obvious
  fraud early.
- **Honest customers** — faster approvals when evidence is clear.
- **Claim reviewers** — a prioritized queue with reasons attached.
