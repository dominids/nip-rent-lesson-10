"""Manager class for handling apartment management operations."""

from datetime import datetime

from src.models import (
    Apartment,
    ApartmentEvent,
    ApartmentSettlement,
    Bill,
    Parameters,
    Tenant,
    TenantBlacklistEntry,
    TenantSettlement,
    Transfer,
)


class Manager:
    """Manager class responsible for loading data and providing methods
    to manage apartments, tenants, transfers, bills, and apartment events.

    Attributes:
        parameters (Parameters): Configuration object containing file paths and limits.
        apartments (Dict[str, Apartment]): Dictionary of loaded apartment objects.
        tenants (Dict[str, Tenant]): Dictionary of loaded tenant objects.
        transfers (List[Transfer]): List of recorded financial transfers.
        bills (List[Bill]): List of apartment bills (costs).
        tenants_blacklist (List[TenantBlacklistEntry]): List of blacklisted tenants.
        apartment_events (List[ApartmentEvent]): List of maintenance or other events.

    """

    def __init__(self, parameters: Parameters):
        """Initializes the Manager with given parameters and loads data from files.

        Args:
            parameters (Parameters): Object containing paths to JSON data files.

        """
        self.parameters = parameters

        self.apartments: dict[str, Apartment] = {}
        self.tenants: dict[str, Tenant] = {}
        self.transfers: list[Transfer] = []
        self.bills: list[Bill] = []
        self.tenants_blacklist: list[TenantBlacklistEntry] = []
        self.apartment_events: list[ApartmentEvent] = []

        self.load_data()

    def load_data(self):
        """Loads core data from JSON files specified in the configuration.
        Populates apartments, tenants, transfers, bills, and blacklist.
        """
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)
        self.tenants_blacklist = TenantBlacklistEntry.from_json_file(
            self.parameters.tenants_blacklist_json_path,
        )

    def load_additional_data(self):
        """Loads auxiliary data, such as apartment maintenance events, from JSON files."""
        self.apartment_events = ApartmentEvent.from_json_file(
            self.parameters.apartment_events_json_path,
        )

    def generate_apartment_events_report(
        self,
        apartment_key: str,
        only_unsolved: bool = True,
    ) -> list[ApartmentEvent]:
        """Filters and returns events associated with a specific apartment.

        Args:
            apartment_key (str): Unique identifier for the apartment.
            only_unsolved (bool): If True, returns only events that are not yet resolved.

        Returns:
            List[ApartmentEvent]: A list of matching ApartmentEvent objects.

        Raises:
            ValueError: If the provided apartment_key does not exist in the database.

        """
        if apartment_key not in self.apartments:
            raise ValueError(f"Apartment key '{apartment_key}' does not exist")
        return [
            event
            for event in self.apartment_events
            if event.apartment == apartment_key
            and (not event.solved or not only_unsolved)
        ]

    def check_tenants_apartment_keys(self) -> bool:
        """Validates data integrity by checking if every tenant is assigned to an existing apartment.

        Returns:
            bool: True if all tenants have valid apartment keys, False otherwise.

        """
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment(self, apartment_key: str) -> Apartment | None:
        """Retrieves an apartment object by its key.

        Args:
            apartment_key (str): Unique identifier for the apartment.

        Returns:
            Optional[Apartment]: Apartment object if found, otherwise None.

        """
        return self.apartments.get(apartment_key, None)

    def get_apartment_costs(
        self,
        apartment_key: str,
        year: int | None = None,
        month: int | None = None,
    ) -> float | None:
        """Calculates the sum of all bills for a specific apartment within a given timeframe.

        Args:
            apartment_key (str): Unique identifier for the apartment.
            year (Optional[int]): Filter by specific year.
            month (Optional[int]): Filter by specific month (1-12).

        Returns:
            Optional[float]: Total sum of bills in PLN, or None if apartment not found.

        Raises:
            ValueError: If the month is outside the 1-12 range.

        """
        if month is not None and (month < 1 or month > 12):
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = 0.0
        for bill in self.bills:
            if (
                bill.apartment == apartment_key
                and (year is None or bill.settlement_year == year)
                and (month is None or bill.settlement_month == month)
            ):
                total_cost += bill.amount_pln
        return total_cost

    def get_settlement(
        self,
        apartment_key: str,
        year: int,
        month: int,
    ) -> ApartmentSettlement | None:
        """Generates a summary settlement for an apartment for a specific month.

        Args:
            apartment_key (str): Unique identifier for the apartment.
            year (int): Year of the settlement.
            month (int): Month of the settlement (1-12).

        Returns:
            Optional[ApartmentSettlement]: Settlement object containing total due, or None.

        Raises:
            ValueError: If the month is invalid.

        """
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = self.get_apartment_costs(apartment_key, year, month)
        if total_cost is None:
            return None

        return ApartmentSettlement(
            key=f"{apartment_key}-{year}-{month}",
            apartment=apartment_key,
            year=year,
            month=month,
            total_due_pln=total_cost,
        )

    def create_tenants_settlements(
        self,
        apartment_settlement: ApartmentSettlement,
    ) -> list[TenantSettlement] | None:
        """Splits the total apartment costs equally among all tenants currently living there.

        Args:
            apartment_settlement (ApartmentSettlement): The base settlement for the whole apartment.

        Returns:
            Optional[List[TenantSettlement]]: List of individual settlements for each tenant,
            or None if the apartment is invalid. Empty list if no tenants found.

        """
        if apartment_settlement.month < 1 or apartment_settlement.month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_settlement.apartment not in self.apartments:
            return None
        tenants_in_apartment = [
            tenant
            for tenant in self.tenants.values()
            if tenant.apartment == apartment_settlement.apartment
        ]
        if not tenants_in_apartment:
            return []

        return [
            TenantSettlement(
                tenant=tenant.name,
                apartment_settlement=apartment_settlement.key,
                month=apartment_settlement.month,
                year=apartment_settlement.year,
                total_due_pln=apartment_settlement.total_due_pln
                / len(tenants_in_apartment),
            )
            for tenant in tenants_in_apartment
        ]

    def get_debtors(self, apartment_key: str, year: int, month: int) -> list[str]:
        """Identifies tenants who have not fully paid their share for a given period.

        Args:
            apartment_key (str): Unique identifier for the apartment.
            year (int): Settlement year.
            month (int): Settlement month.

        Returns:
            List[str]: List of names of tenants with outstanding balance.

        """
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        output = []
        settlement = self.get_settlement(apartment_key, year, month)
        tenant_settlements = self.create_tenants_settlements(settlement)

        for tenant_settlement in tenant_settlements:
            tenant_transfers = [
                transfer
                for transfer in self.transfers
                if self.tenants[transfer.tenant].name == tenant_settlement.tenant
                and transfer.settlement_year == year
                and transfer.settlement_month == month
            ]
            total_paid = sum(
                transfer.amount_pln
                for transfer in tenant_transfers
                if transfer.settlement_year == year
                and transfer.settlement_month == month
            )
            if total_paid < tenant_settlement.total_due_pln:
                output.append(tenant_settlement.tenant)
        return output

    def calculate_tax(self, year: int, month: int, tax_rate: float) -> float:
        """Calculates the tax due for a specific period based on total income (transfers).

        Args:
            year (int): Year to calculate tax for.
            month (int): Month to calculate tax for.
            tax_rate (float): Tax rate multiplier (e.g., 0.085 for 8.5%).

        Returns:
            float: Rounded tax amount in PLN.

        """
        total_income = sum(
            transfer.amount_pln
            for transfer in self.transfers
            if transfer.settlement_year == year and transfer.settlement_month == month
        )
        return round(total_income * tax_rate, 0)

    def check_deposits(self) -> float:
        """Compares the total security deposits received versus the total deposits required by contracts.

        Returns:
            float: Difference between actual and required deposits.
            A negative value indicates missing deposit funds.

        """
        total_deposits = 0.0
        total_due = 0.0
        for _, tenant in self.tenants.items():
            total_deposits += sum(
                transfer.amount_pln
                for transfer in self.transfers
                if self.tenants[transfer.tenant].name == tenant.name
                and transfer.type == "deposit"
            )
            total_due += tenant.deposit_pln

        return total_deposits - total_due

    def get_annual_balance(self, year: int) -> float:
        """Calculates the net profit/loss for a given year (Income - Costs).

        Args:
            year (int): Year for the balance sheet.

        Returns:
            float: Annual balance in PLN.

        """
        total_income = sum(
            transfer.amount_pln
            for transfer in self.transfers
            if transfer.settlement_year == year
        )
        total_due = sum(
            bill.amount_pln for bill in self.bills if bill.settlement_year == year
        )
        return total_income - total_due

    def has_any_bills(self, apartment_key: str, year: int, month: int) -> bool:
        """Checks if there is at least one bill registered for the apartment in a given period.

        Args:
            apartment_key (str): Unique identifier for the apartment.
            year (int): Year to check.
            month (int): Month to check.

        Returns:
            bool: True if bills exist, False otherwise.

        """
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            raise ValueError("Apartment key does not exist")
        return any(
            bill
            for bill in self.bills
            if bill.apartment == apartment_key
            and bill.settlement_year == year
            and bill.settlement_month == month
        )

    def check_transfers_amount_range(self) -> bool:
        """Validates if all transfer amounts are within the safety limits defined in parameters.

        Returns:
            bool: True if all transfers are within limits, False if any transfer is suspicious.

        """
        for transfer in self.transfers:
            if (
                transfer.amount_pln > self.parameters.max_transfer_pln
                or transfer.amount_pln < -self.parameters.max_refund_pln
            ):
                return False
        return True

    def check_tenant_blacklist(self, tenant_name: str) -> bool:
        """Checks if a person is on the internal tenant blacklist.

        Args:
            tenant_name (str): Full name of the tenant.

        Returns:
            bool: True if the tenant is blacklisted, False otherwise.

        """
        return any(
            entry for entry in self.tenants_blacklist if entry.tenant == tenant_name
        )

    def check_transfers_tenant(self) -> bool:
        """Verifies that every transfer is linked to a valid tenant and that the
        settlement date falls within the tenant's agreement period.

        Returns:
            bool: True if all transfers are valid, False otherwise.

        """
        for transfer in self.transfers:
            if transfer.tenant not in self.tenants:
                return False
            if (
                transfer.settlement_year is not None
                and transfer.settlement_month is not None
            ):
                agreement_from = self.tenants[transfer.tenant].date_agreement_from
                agreement_from = datetime.strptime(agreement_from, "%Y-%m-%d").date()
                agreement_to = self.tenants[transfer.tenant].date_agreement_to
                agreement_to = datetime.strptime(agreement_to, "%Y-%m-%d").date()

                # Simple boundary check for year
                if (transfer.settlement_year < agreement_from.year) or (
                    transfer.settlement_year > agreement_to.year
                ):
                    return False

        return True
