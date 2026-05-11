"""NIP Rent: apartment rental settlement toolkit.

The :mod:`src` package is the core domain layer of the project. It models the
data used in a small rental management workflow and exposes business logic for
loading records, validating consistency, and producing financial summaries.

Project purpose
---------------
NIP Rent is an educational, test-driven Python project that demonstrates how to:

- organize a domain model with ``pydantic`` types,
- process JSON-based business data,
- implement clear service-style logic in a manager class,
- verify behavior with unit, integration, functional, and performance tests.

The domain represents apartment rentals: apartments, rooms, tenants, bills,
transfers, blacklist entries, and apartment events.

Package structure
-----------------
- ``src.models`` defines all domain entities and configuration parameters.
- ``src.manager`` provides orchestration and reporting logic on top of models.

How the package is used
-----------------------
Typical flow:

1. Build a :class:`src.models.Parameters` object with data file paths and
        numeric limits.
2. Create :class:`src.manager.Manager` with these parameters.
3. Use manager methods to compute settlements, detect debtors, validate input
        integrity, and calculate balances or taxes.

Data is loaded from JSON files in the ``data/`` directory, then transformed into
typed model instances. This keeps business operations explicit and easier to
test than working with raw dictionaries.

Highlights
----------
- Strongly typed domain models for safer data handling.
- Focused manager API for common settlement and validation operations.
- Clean separation between data schema and business rules.
- Ready for automatic API documentation with ``pdoc``.

Authors
------
- Łukasz Kułacz - initial implementation, testing, documentation,
- Dominik Kłyszyński

"""
