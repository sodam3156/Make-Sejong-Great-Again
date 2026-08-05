namespace Tats.Game.UI.NewGame
{
    /// <summary>
    /// 시작 교차로 하나. <see cref="IntersectionId"/>는 backend/content/map_eojin_playable.json의
    /// startIntersectionIds 값과 같고, <see cref="DisplayName"/>은 같은 파일 intersections[].name이다.
    /// </summary>
    public readonly struct NewGameStartOption
    {
        public string IntersectionId { get; }
        public string DisplayName { get; }

        public NewGameStartOption(string intersectionId, string displayName)
        {
            IntersectionId = intersectionId;
            DisplayName = displayName;
        }
    }
}
