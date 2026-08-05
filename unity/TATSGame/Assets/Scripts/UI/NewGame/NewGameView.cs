using System;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.NewGame
{
    /// <summary>
    /// NewGameScreen.uxml을 그리는 UIDocument에 붙는 얇은 부트스트랩. 서버 연결 없이 뜬다
    /// (docs/23_TITLE_SCREEN_BACKLOG.md T2). 시작 화면과의 실제 화면 전환(어느 UIDocument를 보이고
    /// 숨길지)은 Unity Editor에서 씬을 구성해야 하는 사람 몫으로 남긴다 — T1과 같은 이유다.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed class NewGameView : MonoBehaviour
    {
        NewGamePresenter _presenter;

        public event Action Back;
        public event Action<NewGameSelection> Confirmed;

        void OnEnable()
        {
            var document = GetComponent<UIDocument>();
            _presenter = new NewGamePresenter(document.rootVisualElement);
            _presenter.Back += OnBack;
            _presenter.Confirmed += OnConfirmed;
        }

        void OnDisable()
        {
            if (_presenter == null)
            {
                return;
            }

            _presenter.Back -= OnBack;
            _presenter.Confirmed -= OnConfirmed;
            _presenter.Dispose();
            _presenter = null;
        }

        void OnBack()
        {
            Back?.Invoke();
        }

        void OnConfirmed(NewGameSelection selection)
        {
            Confirmed?.Invoke(selection);
        }
    }
}
