namespace IntrospectionTwin.Twin

/-- One tool invocation observed outside the twin. -/
structure ToolRecord where
  binaryUri : String
  digestSHA256 : String
  exitCode : UInt32
deriving Repr, DecidableEq, Inhabited

/-- External observation. The twin does not originate these records. -/
structure Observation where
  sequenceId : Nat
  timestamp : Nat
  agentId : String
  command : String
  outputBytes : Nat
  toolRecord : ToolRecord
  inputDigest : String
  outputDigest : String
deriving Repr, DecidableEq, Inhabited

end IntrospectionTwin.Twin
