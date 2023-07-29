import pytest
from lib.sql_code_parser import SqlCodeParser
import pandas as pd
import re

@pytest.fixture(scope="module")
def sql_code_parser():
    # Setup logic
    instance = SqlCodeParser(
        source_directory="source_code/sql_server",
        source_file_glob_pattern="**/*.sql",
        chunk_limit=2,
        verbose=True,
    )

    # Your test will run here
    yield instance

    # Teardown logic


def test_sql_code_parser(sql_code_parser):
    df = sql_code_parser.find_ddl_statements()
    assert df.columns.tolist() == ["db_object_name", "ddl_operation", "sql_code"]
    assert len(df) >= 2


def test_extracting_procedure_from_code(sql_code_parser):
    code = """

GO

CREATE PROCEDURE CustOrdersDetail @OrderID int
AS
SELECT ProductName,
    UnitPrice=ROUND(Od.UnitPrice, 2),
    Quantity,
    Discount=CONVERT(int, Discount * 100), 
    ExtendedPrice=ROUND(CONVERT(money, Quantity * (1 - Discount) * Od.UnitPrice), 2)
FROM Products P, [Order Details] Od
WHERE Od.ProductID = P.ProductID and Od.OrderID = @OrderID
go


if exists (select * from sysobjects where id = object_id('dbo.CustOrdersOrders'))
    drop procedure dbo.CustOrdersOrders
GO

CREATE PROCEDURE CustOrdersOrders @CustomerID nchar(5)
AS
SELECT OrderID, 
    OrderDate,
    RequiredDate,
    ShippedDate
FROM Orders
WHERE CustomerID = @CustomerID
ORDER BY OrderID
GO


if exists (select * from sysobjects where id = object_id('dbo.CustOrderHist') and sysstat & 0xf = 4)
    drop procedure dbo.CustOrderHist
GO
CREATE PROCEDURE CustOrderHist @CustomerID nchar(5)
AS
SELECT ProductName, Total=SUM(Quantity)
FROM Products P, [Order Details] OD, Orders O, Customers C
WHERE C.CustomerID = @CustomerID
AND C.CustomerID = O.CustomerID AND O.OrderID = OD.OrderID AND OD.ProductID = P.ProductID
GROUP BY ProductName
GO

if exists (select * from sysobjects where id = object_id('dbo.SalesByCategory') and sysstat & 0xf = 4)
    drop procedure dbo.SalesByCategory
GO
CREATE PROCEDURE SalesByCategory
    @CategoryName nvarchar(15), @OrdYear nvarchar(4) = '1998'
AS
IF @OrdYear != '1996' AND @OrdYear != '1997' AND @OrdYear != '1998' 
BEGIN
    SELECT @OrdYear = '1998'
END

SELECT ProductName,
    TotalPurchase=ROUND(SUM(CONVERT(decimal(14,2), OD.Quantity * (1-OD.Discount) * OD.UnitPrice)), 0)
FROM [Order Details] OD, Orders O, Products P, Categories C
WHERE OD.OrderID = O.OrderID 
    AND OD.ProductID = P.ProductID 
    AND P.CategoryID = C.CategoryID
    AND C.CategoryName = @CategoryName
    AND SUBSTRING(CONVERT(nvarchar(22), O.OrderDate, 111), 1, 4) = @OrdYear
GROUP BY ProductName
ORDER BY ProductName

    """

    segment = sql_code_parser._extract_procedure_declaration_from_code("CustOrdersDetail", code)
    print(f"Segment:\n{segment}")
    assert segment.startswith("CREATE PROCEDURE CustOrdersDetail")
    assert len(re.findall(r'^GO$', segment, re.MULTILINE | re.IGNORECASE)) == 1, "There should be only one GO statement in the extracted segment"

    segment = sql_code_parser._extract_procedure_declaration_from_code("CustOrderHist", code)
    print(f"Segment:\n{segment}")
    assert segment.startswith("CREATE PROCEDURE CustOrderHist @CustomerID nchar(5)")
    assert len(re.findall(r'^GO$', segment, re.MULTILINE | re.IGNORECASE)) == 1, "There should be only one GO statement in the extracted segment"

    # This one tests situations where there are no more GO statements in the file, the last procedure
    segment = sql_code_parser._extract_procedure_declaration_from_code("SalesByCategory", code)
    print(f"Segment:\n{segment}")
    assert segment.startswith("CREATE PROCEDURE SalesByCategory")
    assert "ORDER BY ProductName" in segment, "The last part of the stored procedure was found"
    assert len(re.findall(r'^GO$', segment, re.MULTILINE | re.IGNORECASE)) == 0, "There should be no GO statement in the extracted segment, for this example"

