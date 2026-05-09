# Location Recommendation Capability

## ADDED Requirements

### Requirement: Direct location share returns nearby results

When a user shares a WeChat location, the system SHALL directly return nearby stores within 20km radius.

#### Scenario: User shares WeChat location

- **WHEN** user sends a WeChat location message (detected as text with address)
- **THEN** the system SHALL geocode the address via Amap
- **AND** SHALL return stores within 20km sorted by distance from the closest address
- **AND** SHALL show distance, closest address, and dishes for each store

#### Scenario: Nearby query via text

- **WHEN** user sends "附近有什么好吃的？"
- **AND** the system has no location data
- **THEN** the system SHALL respond asking the user to share their WeChat location

#### Scenario: Distance calculated from closest address

- **WHEN** a store has multiple addresses with coordinates
- **THEN** the system SHALL calculate distance using the address closest to the user
- **AND** SHALL display that closest address in the response
