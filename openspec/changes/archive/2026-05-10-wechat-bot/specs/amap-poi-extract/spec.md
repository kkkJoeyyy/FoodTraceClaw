# Amap POI Extraction Capability

## ADDED Requirements

### Requirement: Amap POI search for store location

During extraction, the system SHALL search Amap POI API for each new store's address and coordinates.

#### Scenario: POI search finds store

- **WHEN** a new store "滋粥楼" is extracted with location "广州"
- **THEN** the system SHALL query Amap place/text API with keywords and city
- **AND** SHALL store addresses as JSON array with coordinates: `[{"addr":"...", "lat":..., "lon":...}]`

#### Scenario: POI search finds multiple addresses

- **WHEN** Amap returns multiple POI results for a store (chain/large restaurant)
- **THEN** the system SHALL store all unique addresses in the JSON array
- **AND** SHALL create only ONE store row (not one per address)

#### Scenario: POI search finds nothing

- **WHEN** Amap returns no results for a store
- **THEN** the system SHALL skip that store (do not store with city-center coordinates)

#### Scenario: Parallel POI search with rate limiting

- **WHEN** extracting many stores at once
- **THEN** the system SHALL search POI in parallel (semaphore: 2, rate: 3 req/s)
- **AND** SHALL not exceed Amap API rate limits
