<?php

namespace App\Model;

use PDO;
use PDOStatement;
use RuntimeException;

class SQLite
{

    private PDO $pdo;
    private PDOStatement|null $stmt = null;
    private array $params = [];

    public function __construct(string $source = root . "/protokolle.db")
    {
        $this->pdo = new PDO("sqlite:$source");
        $this->pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    }

    public function prepare(string $sql): static
    {
        $this->stmt = $this->pdo->prepare($sql);
        $this->params = [];
        return $this;
    }

    public function bindParams(array $params): static
    {
        $this->params = $params;
        return $this;
    }

    public function flush(): bool
    {
        if (!$this->stmt) {
            throw new RuntimeException("No prepared statement.");
        }
        return $this->stmt->execute($this->params);
    }

    public function begin(): void
    {
        $this->pdo->beginTransaction();
    }

    public function commit(): void
    {
        $this->pdo->commit();
    }

    public function rollback(): void
    {
        $this->pdo->rollBack();
    }

    public function fetchAll(): array
    {
        return $this->stmt?->fetchAll(PDO::FETCH_ASSOC) ?? [];
    }

    public function lastInsertId(): string
    {
        return $this->pdo->lastInsertId();
    }

}