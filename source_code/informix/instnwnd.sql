-- This script does not create a database.
-- Run this script in the database you want the objects to be created.
-- Default schema is dbo.

-- Informix doesn't support the SET NOCOUNT, SET QUOTED_IDENTIFIER, and SET DATEFORMAT commands, so they are omitted.

-- Informix doesn't support the sysobjects system view, so we use the systables system catalog table instead.
-- Also, Informix doesn't support the DROP PROCEDURE command, so we use the DROP PROCEDURE IF EXISTS command instead.

/*
	SQL Server to Informix type conversions used:
	1. `int` in SQL Server was converted to `INT` in Informix.
	2. `nvarchar` in SQL Server was converted to `VARCHAR` in Informix. The length of the string was preserved.
	3. `bit` in SQL Server was converted to `SMALLINT` in Informix.
	4. `datetime` in SQL Server was converted to `DATETIME YEAR TO FRACTION(5)` in Informix.
	5. `money` in SQL Server was converted to `DECIMAL(19,4)` in Informix.
	6. `real` in SQL Server was converted to `FLOAT` in Informix.
	7. `uniqueidentifier` in SQL Server was converted to `CHAR(36)` in Informix.
	8. `smallint` in SQL Server was converted to `SMALLINT` in Informix.
	9. `image` in SQL Server was converted to `BYTE` in Informix.
	10. `IDENTITY` keyword in SQL Server was replaced with `SERIAL` data type in Informix for auto-incrementing integer values.

	Please note that these conversions are based on the closest matching data types available in Informix. 
	Some data types in SQL Server do not have a direct equivalent in Informix, and the chosen Informix data types might not behave exactly the same way as their SQL Server counterparts.
*/

DROP PROCEDURE IF EXISTS "Employee Sales by Country";
DROP PROCEDURE IF EXISTS "Sales by Year";
DROP PROCEDURE IF EXISTS "Ten Most Expensive Products";
DROP PROCEDURE IF EXISTS "CustOrderHist";
DROP PROCEDURE IF EXISTS "CustOrdersDetail";
DROP PROCEDURE IF EXISTS "CustOrdersOrders";
DROP PROCEDURE IF EXISTS "SalesByCategory";

-- Informix doesn't support the DROP VIEW command, so we use the DROP VIEW IF EXISTS command instead.

DROP VIEW IF EXISTS "Category Sales for 1997";
DROP VIEW IF EXISTS "Sales by Category";
DROP VIEW IF EXISTS "Sales Totals by Amount";
DROP VIEW IF EXISTS "Summary of Sales by Quarter";
DROP VIEW IF EXISTS "Summary of Sales by Year";
DROP VIEW IF EXISTS "Invoices";
DROP VIEW IF EXISTS "Order Details Extended";
DROP VIEW IF EXISTS "Order Subtotals";
DROP VIEW IF EXISTS "Product Sales for 1997";
DROP VIEW IF EXISTS "Alphabetical list of products";
DROP VIEW IF EXISTS "Current Product List";
DROP VIEW IF EXISTS "Orders Qry";
DROP VIEW IF EXISTS "Products Above Average Price";
DROP VIEW IF EXISTS "Products by Category";
DROP VIEW IF EXISTS "Quarterly Orders";
DROP VIEW IF EXISTS "Customer and Suppliers by City";

-- Informix doesn't support the DROP TABLE command, so we use the DROP TABLE IF EXISTS command instead.

DROP TABLE IF EXISTS "Order Details";
DROP TABLE IF EXISTS "Orders";
DROP TABLE IF EXISTS "Products";
DROP TABLE IF EXISTS "Categories";
DROP TABLE IF EXISTS "CustomerCustomerDemo";
DROP TABLE IF EXISTS "CustomerDemographics";
DROP TABLE IF EXISTS "Customers";
DROP TABLE IF EXISTS "Shippers";
DROP TABLE IF EXISTS "Suppliers";
DROP TABLE IF EXISTS "EmployeeTerritories";
DROP TABLE IF EXISTS "Territories";
DROP TABLE IF EXISTS "Region";
DROP TABLE IF EXISTS "Employees";


CREATE TABLE "Employees" (
	"EmployeeID" SERIAL NOT NULL ,
	"LastName" VARCHAR(20) NOT NULL ,
	"FirstName" VARCHAR(10) NOT NULL ,
	"Title" VARCHAR(30) NULL ,
	"TitleOfCourtesy" VARCHAR(25) NULL ,
	"BirthDate" DATETIME YEAR TO FRACTION NULL ,
	"HireDate" DATETIME YEAR TO FRACTION NULL ,
	"Address" VARCHAR(60) NULL ,
	"City" VARCHAR(15) NULL ,
	"Region" VARCHAR(15) NULL ,
	"PostalCode" VARCHAR(10) NULL ,
	"Country" VARCHAR(15) NULL ,
	"HomePhone" VARCHAR(24) NULL ,
	"Extension" VARCHAR(4) NULL ,
	"Photo" BYTE NULL , -- type conversion needed
	"Notes" TEXT NULL , -- type conversion needed
	"ReportsTo" INT NULL ,
	"PhotoPath" VARCHAR(255) NULL ,
	PRIMARY KEY ("EmployeeID")
);

CREATE INDEX "LastName" ON "Employees"("LastName");
CREATE INDEX "PostalCode" ON "Employees"("PostalCode");

CREATE TABLE "Categories" (
	"CategoryID" SERIAL NOT NULL ,
	"CategoryName" VARCHAR(15) NOT NULL ,
	"Description" TEXT NULL , -- type conversion needed
	"Picture" BYTE NULL , -- type conversion needed
	PRIMARY KEY ("CategoryID")
);

CREATE INDEX "CategoryName" ON "Categories"("CategoryName");

CREATE TABLE "Suppliers" (
	"SupplierID" SERIAL PRIMARY KEY NOT NULL,
	"CompanyName" NVARCHAR(40) NOT NULL,
	"ContactName" NVARCHAR(30),
	"ContactTitle" NVARCHAR(30),
	"Address" NVARCHAR(60),
	"City" NVARCHAR(15),
	"Region" NVARCHAR(15),
	"PostalCode" NVARCHAR(10),
	"Country" NVARCHAR(15),
	"Phone" NVARCHAR(24),
	"Fax" NVARCHAR(24),
	"HomePage" TEXT -- type conversion needed
);

CREATE INDEX "CompanyName" ON "Suppliers"("CompanyName");
CREATE INDEX "PostalCode" ON "Suppliers"("PostalCode");

CREATE TABLE "Orders" (
	"OrderID" SERIAL PRIMARY KEY NOT NULL,
	"CustomerID" CHAR(5),
	"EmployeeID" INT,
	"OrderDate" DATETIME YEAR TO FRACTION,
	"RequiredDate" DATETIME YEAR TO FRACTION,
	"ShippedDate" DATETIME YEAR TO FRACTION,
	"ShipVia" INT,
	"Freight" DECIMAL(19,4) DEFAULT 0,
	"ShipName" NVARCHAR(40),
	"ShipAddress" NVARCHAR(60),
	"ShipCity" NVARCHAR(15),
	"ShipRegion" NVARCHAR(15),
	"ShipPostalCode" NVARCHAR(10),
	"ShipCountry" NVARCHAR(15),
	FOREIGN KEY ("CustomerID") REFERENCES "Customers" ("CustomerID"),
	FOREIGN KEY ("EmployeeID") REFERENCES "Employees" ("EmployeeID"),
	FOREIGN KEY ("ShipVia") REFERENCES "Shippers" ("ShipperID")
);

CREATE INDEX "CustomerID" ON "Orders"("CustomerID");
CREATE INDEX "CustomersOrders" ON "Orders"("CustomerID");
CREATE INDEX "EmployeeID" ON "Orders"("EmployeeID");
CREATE INDEX "EmployeesOrders" ON "Orders"("EmployeeID");
CREATE INDEX "OrderDate" ON "Orders"("OrderDate");
CREATE INDEX "ShippedDate" ON "Orders"("ShippedDate");
CREATE INDEX "ShippersOrders" ON "Orders"("ShipVia");
CREATE INDEX "ShipPostalCode" ON "Orders"("ShipPostalCode");

CREATE TABLE "Products" (
	"ProductID" SERIAL PRIMARY KEY NOT NULL,
	"ProductName" NVARCHAR(40) NOT NULL,
	"SupplierID" INT,
	"CategoryID" INT,
	"QuantityPerUnit" NVARCHAR(20),
	"UnitPrice" DECIMAL(19,4) DEFAULT 0,
	"UnitsInStock" SMALLINT DEFAULT 0,
	"UnitsOnOrder" SMALLINT DEFAULT 0,
	"ReorderLevel" SMALLINT DEFAULT 0,
	"Discontinued" SMALLINT NOT NULL DEFAULT 0, -- bit converted to SMALLINT
	FOREIGN KEY ("CategoryID") REFERENCES "Categories" ("CategoryID"),
	FOREIGN KEY ("SupplierID") REFERENCES "Suppliers" ("SupplierID"),
	CHECK (UnitPrice >= 0),
	CHECK (ReorderLevel >= 0),
	CHECK (UnitsInStock >= 0),
	CHECK (UnitsOnOrder >= 0)
);

CREATE INDEX "CategoriesProducts" ON "Products"("CategoryID");
CREATE INDEX "CategoryID" ON "Products"("CategoryID");
CREATE INDEX "ProductName" ON "Products"("ProductName");
CREATE INDEX "SupplierID" ON "Products"("SupplierID");
CREATE INDEX "SuppliersProducts" ON "Products"("SupplierID");

-- Continued...

CREATE TABLE "Order Details" (
	"OrderID" INT NOT NULL,
	"ProductID" INT NOT NULL,
	"UnitPrice" DECIMAL(19,4) DEFAULT 0,
	"Quantity" SMALLINT DEFAULT 1,
	"Discount" FLOAT DEFAULT 0,
	PRIMARY KEY ("OrderID", "ProductID"),
	FOREIGN KEY ("OrderID") REFERENCES "Orders" ("OrderID"),
	FOREIGN KEY ("ProductID") REFERENCES "Products" ("ProductID"),
	CHECK (UnitPrice >= 0),
	CHECK (Quantity > 0),
	CHECK (Discount BETWEEN 0 AND 1)
);

CREATE INDEX "OrdersOrder Details" ON "Order Details"("OrderID");
CREATE INDEX "ProductsOrder Details" ON "Order Details"("ProductID");

CREATE TABLE "CustomerCustomerDemo" (
	"CustomerID" CHAR(5) NOT NULL,
	"CustomerTypeID" CHAR(10) NOT NULL,
	PRIMARY KEY ("CustomerID", "CustomerTypeID"),
	FOREIGN KEY ("CustomerID") REFERENCES "Customers" ("CustomerID"),
	FOREIGN KEY ("CustomerTypeID") REFERENCES "CustomerDemographics" ("CustomerTypeID")
);

CREATE INDEX "CustomerDemographicsCustomerCustomerDemo" ON "CustomerCustomerDemo"("CustomerTypeID");
CREATE INDEX "CustomersCustomerCustomerDemo" ON "CustomerCustomerDemo"("CustomerID");

CREATE TABLE "Region" (
	"RegionID" SERIAL PRIMARY KEY NOT NULL,
	"RegionDescription" CHAR(50) NOT NULL
);

CREATE TABLE "Territories" (
	"TerritoryID" SERIAL PRIMARY KEY NOT NULL,
	"TerritoryDescription" CHAR(50) NOT NULL,
	"RegionID" INT NOT NULL,
	FOREIGN KEY ("RegionID") REFERENCES "Region" ("RegionID")
);

CREATE INDEX "RegionTerritories" ON "Territories"("RegionID");

CREATE TABLE "EmployeeTerritories" (
	"EmployeeID" INT NOT NULL,
	"TerritoryID" INT NOT NULL,
	PRIMARY KEY ("EmployeeID", "TerritoryID"),
	FOREIGN KEY ("EmployeeID") REFERENCES "Employees" ("EmployeeID"),
	FOREIGN KEY ("TerritoryID") REFERENCES "Territories" ("TerritoryID")
);

CREATE INDEX "EmployeesEmployeeTerritories" ON "EmployeeTerritories"("EmployeeID");
CREATE INDEX "TerritoriesEmployeeTerritories" ON "EmployeeTerritories"("TerritoryID");

-- continued...

CREATE TABLE "Order Details" (
	"OrderID" INT NOT NULL ,
	"ProductID" INT NOT NULL ,
	"UnitPrice" DECIMAL(19,4) NOT NULL DEFAULT 0,
	"Quantity" SMALLINT NOT NULL DEFAULT 1,
	"Discount" FLOAT NOT NULL DEFAULT 0,
	PRIMARY KEY ("OrderID", "ProductID"),
	FOREIGN KEY ("OrderID") REFERENCES "Orders" ("OrderID"),
	FOREIGN KEY ("ProductID") REFERENCES "Products" ("ProductID"),
	CHECK (Discount >= 0 AND Discount <= 1),
	CHECK (Quantity > 0),
	CHECK (UnitPrice >= 0)
);

CREATE INDEX "OrderID" ON "Order Details"("OrderID");
CREATE INDEX "OrdersOrder_Details" ON "Order Details"("OrderID");
CREATE INDEX "ProductID" ON "Order Details"("ProductID");
CREATE INDEX "ProductsOrder_Details" ON "Order Details"("ProductID");

CREATE VIEW "Customer and Suppliers by City" AS
SELECT City, CompanyName, ContactName, 'Customers' AS Relationship 
FROM Customers
UNION 
SELECT City, CompanyName, ContactName, 'Suppliers'
FROM Suppliers;

CREATE VIEW "Alphabetical list of products" AS
SELECT Products.*, Categories.CategoryName
FROM Categories INNER JOIN Products ON Categories.CategoryID = Products.CategoryID
WHERE Products.Discontinued = 0;

CREATE VIEW "Current Product List" AS
SELECT Product_List.ProductID, Product_List.ProductName
FROM Products AS Product_List
WHERE Product_List.Discontinued = 0;

CREATE VIEW "Orders Qry" AS
SELECT Orders.OrderID, Orders.CustomerID, Orders.EmployeeID, Orders.OrderDate, Orders.RequiredDate, 
	Orders.ShippedDate, Orders.ShipVia, Orders.Freight, Orders.ShipName, Orders.ShipAddress, Orders.ShipCity, 
	Orders.ShipRegion, Orders.ShipPostalCode, Orders.ShipCountry, 
	Customers.CompanyName, Customers.Address, Customers.City, Customers.Region, Customers.PostalCode, Customers.Country
FROM Customers INNER JOIN Orders ON Customers.CustomerID = Orders.CustomerID;

CREATE VIEW "Products Above Average Price" AS
SELECT Products.ProductName, Products.UnitPrice
FROM Products
WHERE Products.UnitPrice > (SELECT AVG(UnitPrice) From Products);

CREATE VIEW "Products by Category" AS
SELECT Categories.CategoryName, Products.ProductName, Products.QuantityPerUnit, Products.UnitsInStock, Products.Discontinued
FROM Categories INNER JOIN Products ON Categories.CategoryID = Products.CategoryID
WHERE Products.Discontinued <> 1;

CREATE VIEW "Quarterly Orders" AS
SELECT DISTINCT Customers.CustomerID, Customers.CompanyName, Customers.City, Customers.Country
FROM Customers RIGHT JOIN Orders ON Customers.CustomerID = Orders.CustomerID
WHERE Orders.OrderDate BETWEEN '19970101' And '19971231';


CREATE VIEW Invoices AS
SELECT Orders.ShipName, Orders.ShipAddress, Orders.ShipCity, Orders.ShipRegion, Orders.ShipPostalCode, 
	Orders.ShipCountry, Orders.CustomerID, Customers.CompanyName AS CustomerName, Customers.Address, Customers.City, 
	Customers.Region, Customers.PostalCode, Customers.Country, 
	(FirstName || ' ' || LastName) AS Salesperson, 
	Orders.OrderID, Orders.OrderDate, Orders.RequiredDate, Orders.ShippedDate, Shippers.CompanyName As ShipperName, 
	"Order Details".ProductID, Products.ProductName, "Order Details".UnitPrice, "Order Details".Quantity, 
	"Order Details".Discount, 
	(("Order Details".UnitPrice * Quantity * (1 - Discount) / 100) * 100) AS ExtendedPrice, Orders.Freight
FROM 	Shippers, 
		Products, 
		Employees, 
		Customers, 
		Orders, 
		"Order Details"
WHERE 	Customers.CustomerID = Orders.CustomerID AND 
		Employees.EmployeeID = Orders.EmployeeID AND 
		Orders.OrderID = "Order Details".OrderID AND 
		Products.ProductID = "Order Details".ProductID AND 
		Shippers.ShipperID = Orders.ShipVia;


CREATE VIEW "Order Details Extended" AS
SELECT "Order Details".OrderID, "Order Details".ProductID, Products.ProductName, 
	"Order Details".UnitPrice, "Order Details".Quantity, "Order Details".Discount, 
	(("Order Details".UnitPrice * Quantity * (1 - Discount) / 100) * 100) AS ExtendedPrice
FROM Products, "Order Details"
WHERE Products.ProductID = "Order Details".ProductID;

CREATE VIEW "Order Subtotals" AS
SELECT "Order Details".OrderID, Sum(("Order Details".UnitPrice * Quantity * (1 - Discount) / 100) * 100) AS Subtotal
FROM "Order Details"
GROUP BY "Order Details".OrderID;

CREATE VIEW "Product Sales for 1997" AS
SELECT Categories.CategoryName, Products.ProductName, 
Sum(("Order Details".UnitPrice * Quantity * (1 - Discount) / 100) * 100) AS ProductSales
FROM Categories, Products, Orders, "Order Details"
WHERE Categories.CategoryID = Products.CategoryID AND 
	Orders.OrderID = "Order Details".OrderID AND 
	Products.ProductID = "Order Details".ProductID AND 
	(Orders.ShippedDate BETWEEN '1997-01-01' AND '1997-12-31')
GROUP BY Categories.CategoryName, Products.ProductName;

CREATE VIEW "Category Sales for 1997" AS
SELECT "Product Sales for 1997".CategoryName, Sum("Product Sales for 1997".ProductSales) AS CategorySales
FROM "Product Sales for 1997"
GROUP BY "Product Sales for 1997".CategoryName;

CREATE VIEW "Sales by Category" AS
SELECT Categories.CategoryID, Categories.CategoryName, Products.ProductName, 
	Sum("Order Details Extended".ExtendedPrice) AS ProductSales
FROM 	Categories, Products, Orders, "Order Details Extended"
WHERE Categories.CategoryID = Products.CategoryID AND 
	Orders.OrderID = "Order Details Extended".OrderID AND 
	Products.ProductID = "Order Details Extended".ProductID AND 
	(Orders.OrderDate BETWEEN '1997-01-01' AND '1997-12-31')
GROUP BY Categories.CategoryID, Categories.CategoryName, Products.ProductName;

-- continued...

CREATE VIEW "Sales Totals by Amount" AS
SELECT "Order Subtotals".Subtotal AS SaleAmount, Orders.OrderID, Customers.CompanyName, Orders.ShippedDate
FROM 	Customers, Orders, "Order Subtotals"
WHERE Customers.CustomerID = Orders.CustomerID AND 
	Orders.OrderID = "Order Subtotals".OrderID AND 
	("Order Subtotals".Subtotal > 2500) AND 
	(Orders.ShippedDate BETWEEN '1997-01-01' AND '1997-12-31');

CREATE VIEW "Summary of Sales by Quarter" AS
SELECT Orders.ShippedDate, Orders.OrderID, "Order Subtotals".Subtotal
FROM Orders, "Order Subtotals"
WHERE Orders.OrderID = "Order Subtotals".OrderID AND 
	Orders.ShippedDate IS NOT NULL;

CREATE VIEW "Summary of Sales by Year" AS
SELECT Orders.ShippedDate, Orders.OrderID, "Order Subtotals".Subtotal
FROM Orders, "Order Subtotals"
WHERE Orders.OrderID = "Order Subtotals".OrderID AND 
	Orders.ShippedDate IS NOT NULL;


CREATE PROCEDURE "Ten Most Expensive Products"()
RETURNING CHAR(40), DECIMAL(14,2);
SELECT FIRST 10 Products.ProductName AS TenMostExpensiveProducts, Products.UnitPrice
FROM Products
ORDER BY Products.UnitPrice DESC;
END PROCEDURE;


CREATE PROCEDURE "Employee Sales by Country" (Beginning_Date DATETIME YEAR TO FRACTION, Ending_Date DATETIME YEAR TO FRACTION)
RETURNING CHAR(15), CHAR(20), CHAR(10), DATETIME YEAR TO FRACTION, INT, DECIMAL(19,4);
SELECT Employees.Country, Employees.LastName, Employees.FirstName, Orders.ShippedDate, Orders.OrderID, "Order Subtotals".Subtotal AS SaleAmount
FROM Employees, Orders, "Order Subtotals"
WHERE Employees.EmployeeID = Orders.EmployeeID AND 
	Orders.OrderID = "Order Subtotals".OrderID AND 
	Orders.ShippedDate BETWEEN Beginning_Date AND Ending_Date;
END PROCEDURE;


CREATE PROCEDURE "Sales by Year" (Beginning_Date DATETIME YEAR TO FRACTION, Ending_Date DATETIME YEAR TO FRACTION)
RETURNING DATETIME YEAR TO FRACTION, INT, DECIMAL(19,4), CHAR(4);
SELECT Orders.ShippedDate, Orders.OrderID, "Order Subtotals".Subtotal, TO_CHAR(ShippedDate, '%Y') AS Year
FROM Orders, "Order Subtotals"
WHERE Orders.OrderID = "Order Subtotals".OrderID AND 
	Orders.ShippedDate BETWEEN Beginning_Date AND Ending_Date;
END PROCEDURE;

DROP PROCEDURE IF EXISTS CustOrdersDetail;

CREATE PROCEDURE CustOrdersDetail (OrderID INT)
RETURNING CHAR(40), DECIMAL(19,4), SMALLINT, INT, DECIMAL(19,4);
SELECT ProductName,
    ROUND(Od.UnitPrice, 2) AS UnitPrice,
    Quantity,
    Discount * 100::INT AS Discount, 
    ROUND(Quantity * (1 - Discount) * Od.UnitPrice, 2) AS ExtendedPrice
FROM Products P, "Order Details" Od
WHERE Od.ProductID = P.ProductID AND Od.OrderID = OrderID;
END PROCEDURE;

DROP PROCEDURE IF EXISTS CustOrdersOrders;

CREATE PROCEDURE CustOrdersOrders (CustomerID CHAR(5))
RETURNING INT, DATETIME YEAR TO FRACTION, DATETIME YEAR TO FRACTION, DATETIME YEAR TO FRACTION;
SELECT OrderID, 
	OrderDate,
	RequiredDate,
	ShippedDate
FROM Orders
WHERE CustomerID = CustomerID
ORDER BY OrderID;
END PROCEDURE;

DROP PROCEDURE IF EXISTS CustOrderHist;

CREATE PROCEDURE CustOrderHist (CustomerID CHAR(5))
RETURNING CHAR(40), INT;
SELECT ProductName, SUM(Quantity) AS Total
FROM Products P, "Order Details" OD, Orders O, Customers C
WHERE C.CustomerID = CustomerID
AND C.CustomerID = O.CustomerID AND O.OrderID = OD.OrderID AND OD.ProductID = P.ProductID
GROUP BY ProductName;
END PROCEDURE;

DROP PROCEDURE IF EXISTS SalesByCategory;

CREATE PROCEDURE SalesByCategory (CategoryName NVARCHAR(15), OrdYear NVARCHAR(4) DEFAULT '1998')
RETURNING CHAR(40), DECIMAL(14,2);
LET OrdYear = CASE WHEN OrdYear NOT IN ('1996', '1997', '1998') THEN '1998' ELSE OrdYear END;
SELECT ProductName,
	ROUND(SUM(OD.Quantity * (1-OD.Discount) * OD.UnitPrice), 0) AS TotalPurchase
FROM "Order Details" OD, Orders O, Products P, Categories C
WHERE OD.OrderID = O.OrderID 
	AND OD.ProductID = P.ProductID 
	AND P.CategoryID = C.CategoryID
	AND C.CategoryName = CategoryName
	AND YEAR(O.OrderDate) = OrdYear::INT
GROUP BY ProductName
ORDER BY ProductName;
END PROCEDURE;


CREATE TABLE CustomerCustomerDemo 
(
	CustomerID CHAR(5) NOT NULL,
	CustomerTypeID CHAR(10) NOT NULL
);

CREATE TABLE CustomerDemographics 
(
	CustomerTypeID CHAR(10) NOT NULL,
	CustomerDesc TEXT
);

CREATE TABLE Region 
(
	RegionID INT NOT NULL,
	RegionDescription CHAR(50) NOT NULL
);

CREATE TABLE Territories 
(
	TerritoryID NVARCHAR(20) NOT NULL,
	TerritoryDescription CHAR(50) NOT NULL,
	RegionID INT NOT NULL
);

CREATE TABLE EmployeeTerritories 
(
	EmployeeID INT NOT NULL,
	TerritoryID NVARCHAR(20) NOT NULL
);

--  The following adds constraints to the Northwind database

ALTER TABLE CustomerCustomerDemo
	ADD CONSTRAINT PK_CustomerCustomerDemo PRIMARY KEY
	(
		CustomerID,
		CustomerTypeID
	);

ALTER TABLE CustomerDemographics
	ADD CONSTRAINT PK_CustomerDemographics PRIMARY KEY
	(
		CustomerTypeID
	);

ALTER TABLE CustomerCustomerDemo
	ADD CONSTRAINT FK_CustomerCustomerDemo FOREIGN KEY 
	(
		CustomerTypeID
	) REFERENCES CustomerDemographics
	(
		CustomerTypeID
	);

ALTER TABLE CustomerCustomerDemo
	ADD CONSTRAINT FK_CustomerCustomerDemo_Customers FOREIGN KEY
	(
		CustomerID
	) REFERENCES Customers
	(
		CustomerID
	);

ALTER TABLE Region
	ADD CONSTRAINT PK_Region PRIMARY KEY
	(
		RegionID
	);

ALTER TABLE Territories
	ADD CONSTRAINT PK_Territories PRIMARY KEY
	(
		TerritoryID
	);

ALTER TABLE Territories
	ADD CONSTRAINT FK_Territories_Region FOREIGN KEY 
	(
		RegionID
	) REFERENCES Region
	(
		RegionID
	);

ALTER TABLE EmployeeTerritories
	ADD CONSTRAINT PK_EmployeeTerritories PRIMARY KEY
	(
		EmployeeID,
		TerritoryID
	);

ALTER TABLE EmployeeTerritories
	ADD CONSTRAINT FK_EmployeeTerritories_Employees FOREIGN KEY 
	(
		EmployeeID
	) REFERENCES Employees
	(
		EmployeeID
	);

ALTER TABLE EmployeeTerritories	
	ADD CONSTRAINT FK_EmployeeTerritories_Territories FOREIGN KEY 
	(
		TerritoryID
	) REFERENCES Territories
	(
		TerritoryID
	);


CREATE PROCEDURE InsertProduct(
    ProductName NVARCHAR(40),
    SupplierID INT,
    CategoryID INT,
    QuantityPerUnit NVARCHAR(20),
    UnitPrice DECIMAL(10,2),
    UnitsInStock SMALLINT,
    UnitsOnOrder SMALLINT,
    ReorderLevel SMALLINT,
    Discontinued SMALLINT)
BEGIN
    INSERT INTO Products (
        ProductName,
        SupplierID,
        CategoryID,
        QuantityPerUnit,
        UnitPrice,
        UnitsInStock,
        UnitsOnOrder,
        ReorderLevel,
        Discontinued
    )
    VALUES (
        ProductName,
        SupplierID,
        CategoryID,
        QuantityPerUnit,
        UnitPrice,
        UnitsInStock,
        UnitsOnOrder,
        ReorderLevel,
        Discontinued
    );
END;

CREATE PROCEDURE UpdateProduct(
    ProductID INT,
    ProductName NVARCHAR(40),
    SupplierID INT,
    CategoryID INT,
    QuantityPerUnit NVARCHAR(20),
    UnitPrice DECIMAL(10,2),
    UnitsInStock SMALLINT,
    UnitsOnOrder SMALLINT,
    ReorderLevel SMALLINT,
    Discontinued SMALLINT)
BEGIN
    UPDATE Products
    SET ProductName = ProductName,
        SupplierID = SupplierID,
        CategoryID = CategoryID,
        QuantityPerUnit = QuantityPerUnit,
        UnitPrice = UnitPrice,
        UnitsInStock = UnitsInStock,
        UnitsOnOrder = UnitsOnOrder,
        ReorderLevel = ReorderLevel,
        Discontinued = Discontinued
    WHERE ProductID = ProductID;
END;

CREATE PROCEDURE DeleteProduct(
    ProductID INT)
BEGIN
    DELETE FROM Products
    WHERE ProductID = ProductID;
END;

CREATE PROCEDURE InsertOrder(
    CustomerID CHAR(5),
    EmployeeID INT,
    OrderDate DATETIME YEAR TO FRACTION,
    RequiredDate DATETIME YEAR TO FRACTION,
    ShippedDate DATETIME YEAR TO FRACTION,
    ShipVia INT,
    Freight DECIMAL(10,2),
    ShipName NVARCHAR(40),
    ShipAddress NVARCHAR(60),
    ShipCity NVARCHAR(15),
    ShipRegion NVARCHAR(15),
    ShipPostalCode NVARCHAR(10),
    ShipCountry NVARCHAR(15))
BEGIN
    INSERT INTO Orders (
        CustomerID,
        EmployeeID,
        OrderDate,
        RequiredDate,
        ShippedDate,
        ShipVia,
        Freight,
        ShipName,
        ShipAddress,
        ShipCity,
        ShipRegion,
        ShipPostalCode,
        ShipCountry
    )
    VALUES (
        CustomerID,
        EmployeeID,
        OrderDate,
        RequiredDate,
        ShippedDate,
        ShipVia,
        Freight,
        ShipName,
        ShipAddress,
        ShipCity,
        ShipRegion,
        ShipPostalCode,
        ShipCountry
    );
END;

CREATE PROCEDURE UpdateOrder(
    OrderID INT,
    CustomerID CHAR(5),
    EmployeeID INT,
    OrderDate DATETIME YEAR TO FRACTION,
    RequiredDate DATETIME YEAR TO FRACTION,
    ShippedDate DATETIME YEAR TO FRACTION,
    ShipVia INT,
    Freight DECIMAL(10,2),
    ShipName NVARCHAR(40),
    ShipAddress NVARCHAR(60),
    ShipCity NVARCHAR(15),
    ShipRegion NVARCHAR(15),
    ShipPostalCode NVARCHAR(10),
    ShipCountry NVARCHAR(15))
BEGIN
    UPDATE Orders
    SET CustomerID = CustomerID,
        EmployeeID = EmployeeID,
        OrderDate = OrderDate,
        RequiredDate = RequiredDate,
        ShippedDate = ShippedDate,
        ShipVia = ShipVia,
        Freight = Freight,
        ShipName = ShipName,
        ShipAddress = ShipAddress,
        ShipCity = ShipCity,
        ShipRegion = ShipRegion,
        ShipPostalCode = ShipPostalCode,
        ShipCountry = ShipCountry
    WHERE OrderID = OrderID;
END;

CREATE PROCEDURE DeleteOrder(
    OrderID INT)
BEGIN
    DELETE FROM Orders
    WHERE OrderID = OrderID;
END;

CREATE PROCEDURE InsertOrderDetails(
    OrderID INT,
    ProductID INT,
    UnitPrice DECIMAL(10,2),
    Quantity SMALLINT,
    Discount REAL)
BEGIN
    INSERT INTO Order_Details (OrderID, ProductID, UnitPrice, Quantity, Discount)
    VALUES (OrderID, ProductID, UnitPrice, Quantity, Discount);
END;

CREATE PROCEDURE UpdateOrderDetails(
    OrderID INT,
    ProductID INT,
    UnitPrice DECIMAL(10,2),
    Quantity SMALLINT,
    Discount REAL)
BEGIN
    UPDATE Order_Details
    SET UnitPrice = UnitPrice,
        Quantity = Quantity,
        Discount = Discount
    WHERE OrderID = OrderID AND ProductID = ProductID;
END;

CREATE PROCEDURE DeleteOrderDetails(
    OrderID INT,
    ProductID INT)
BEGIN
    DELETE FROM Order_Details
    WHERE OrderID = OrderID AND ProductID = ProductID;
END;

CREATE PROCEDURE ExecuteInsertProduct()
BEGIN
    -- Call the InsertProduct stored procedure with specific parameter values
    EXECUTE PROCEDURE InsertProduct(
        'New Product',
        1,
        2,
        '12 boxes per case',
        10.99,
        50,
        20,
        10,
        0);
END;
