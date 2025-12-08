# 5. Exception Hierarchy

```
AIPatternAnalyzerError (base)
├── DimensionNotFoundError
│   └── Raised when dimension not in registry
│       Attributes: dimension_name
│
├── DuplicateDimensionError
│   └── Raised on duplicate registration attempt
│       Attributes: dimension_name
│
├── InvalidTierError
│   └── Raised when tier is not valid
│       Attributes: tier, valid_tiers
│
├── InvalidWeightError
│   └── Raised when weight outside 0-100
│       Attributes: weight, valid_range
│
└── ParameterLoadError
    └── Raised when parameter config cannot load
        Attributes: config_path

AnalysisError (base)
├── EmptyFileError
│   └── Raised when file has no analyzable content
│
└── InsufficientDataError
    └── Raised when not enough data for analysis
```

---
