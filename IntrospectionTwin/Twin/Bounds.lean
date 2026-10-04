import IntrospectionTwin.Twin.Observation

namespace IntrospectionTwin.Twin

/-- Bounds consulted by `step`.
    Context integrity and state immutability are enforced by `step`, not stored here. -/
structure TwinBounds where
  agentIdentity : String
  allowedTools : List String
  commandAllowlist : List String
  maxGasBudget : Nat
  maxOutputBytes : Nat
deriving Repr, DecidableEq, Inhabited

def satisfiesIdentity (b : TwinBounds) (obs : Observation) : Bool :=
  obs.agentId == b.agentIdentity

def satisfiesToolProvenance (b : TwinBounds) (obs : Observation) : Bool :=
  b.allowedTools.contains obs.toolRecord.digestSHA256

def satisfiesCommand (b : TwinBounds) (obs : Observation) : Bool :=
  b.commandAllowlist.contains obs.command

def satisfiesOutput (b : TwinBounds) (obs : Observation) : Bool :=
  obs.outputBytes ≤ b.maxOutputBytes

end IntrospectionTwin.Twin
